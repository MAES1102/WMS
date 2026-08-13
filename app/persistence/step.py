"""SQLAlchemy adapter for one atomic automatic workflow step."""

from collections.abc import Callable
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.application.errors import StateVersionConflict, StepStateError
from app.application.invoice_validation import (
    InvoiceValidationInput,
)
from app.application.invoice_tasks import InvoiceBusinessSnapshot
from app.application.ports import (
    ArchiveRecordCreated,
    AutomaticStepCommit,
    ExecutionContext,
    InternalNotificationCreated,
    InvoiceMetadataValidated,
    InvoiceStateChanged,
    ReadyAutomaticStep,
    RetryCurrentTask,
)
from app.domain.invoice import InvoiceState, RawInvoiceMetadata
from app.domain.types import (
    TaskDefinition,
    TaskType,
    TerminalDecision,
    TerminalReached,
    TransitionCondition,
    TransitionDefinition,
    TransitionSelected,
)
from app.persistence.models import (
    ArchiveRecord,
    ExecutionCursor,
    Invoice,
    InvoiceTaskAttempt,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    InternalNotification,
    RevisionTask,
    RevisionTransition,
)


class ReadyStepNotFound(LookupError):
    pass


class SqlAlchemyAutomaticStepUnitOfWork:
    """Load executor input and commit one observable step transaction."""

    def __init__(
        self,
        session: Session,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._session = session
        self._id_factory = id_factory or (lambda: str(uuid4()))

    def load_ready_step(self, run_id: str) -> ReadyAutomaticStep:
        run = self._session.get(InvoiceWorkflowRun, run_id)
        cursor = self._session.get(ExecutionCursor, run_id)
        if run is None or cursor is None:
            raise ReadyStepNotFound(f"Run {run_id!r} has no execution cursor")
        if cursor.phase != "READY" or cursor.current_task_id is None:
            raise StepStateError(
                f"Run {run_id!r} is not ready for an automatic step"
            )

        task = self._session.get(RevisionTask, cursor.current_task_id)
        if task is None or task.revision_id != run.revision_id:
            raise StepStateError(
                "Execution cursor does not reference a task in the run revision"
            )
        transitions = self._session.scalars(
            select(RevisionTransition)
            .where(
                RevisionTransition.revision_id == run.revision_id,
                RevisionTransition.from_task_id == task.id,
            )
            .order_by(RevisionTransition.id)
        ).all()
        completed_attempts = self._session.scalar(
            select(func.count())
            .select_from(InvoiceTaskAttempt)
            .where(
                InvoiceTaskAttempt.run_id == run.id,
                InvoiceTaskAttempt.task_id == task.id,
            )
        )
        return ReadyAutomaticStep(
            run_id=run.id,
            invoice_id=run.invoice_id,
            task=TaskDefinition(
                id=task.id,
                name=task.name,
                task_type=TaskType(task.task_type),
                is_start=task.is_start,
                max_attempts=task.max_attempts,
            ),
            transitions=tuple(
                TransitionDefinition(
                    id=transition.id,
                    from_task_id=transition.from_task_id,
                    to_task_id=transition.to_task_id,
                    condition=TransitionCondition(transition.condition),
                )
                for transition in transitions
            ),
            completed_attempts=int(completed_attempts or 0),
            state_version=cursor.state_version,
        )

    def load(self, context: ExecutionContext) -> InvoiceValidationInput:
        run = self._session.get(InvoiceWorkflowRun, context.run_id)
        invoice = self._session.get(Invoice, context.invoice_id)
        if run is None or invoice is None or run.invoice_id != invoice.id:
            raise ReadyStepNotFound(
                "Validation context does not identify one persisted invoice run"
            )
        cursor = self._session.get(ExecutionCursor, context.run_id)
        if cursor is None or cursor.current_task_id != context.task_id:
            raise StepStateError("Validation context is not the current cursor task")
        return InvoiceValidationInput(
            metadata=RawInvoiceMetadata(
                supplier_name=invoice.supplier_name_raw,
                invoice_number=invoice.invoice_number_raw,
                issue_date=invoice.issue_date_raw,
                amount=invoice.amount_raw,
                currency=invoice.currency_raw,
            ),
            document_identity=invoice.document_identity,
            declared_media_type=invoice.declared_media_type,
            document_size_bytes=invoice.document_size_bytes,
        )

    def load_business(self, context: ExecutionContext) -> InvoiceBusinessSnapshot:
        run = self._session.get(InvoiceWorkflowRun, context.run_id)
        invoice = self._session.get(Invoice, context.invoice_id)
        cursor = self._session.get(ExecutionCursor, context.run_id)
        if (
            run is None
            or invoice is None
            or cursor is None
            or run.invoice_id != invoice.id
            or cursor.phase != "READY"
            or cursor.current_task_id != context.task_id
        ):
            raise StepStateError(
                "Business task context does not match one ready invoice run"
            )
        return InvoiceBusinessSnapshot(
            invoice_state=InvoiceState(invoice.state),
            document_identity=invoice.document_identity,
            invoice_number=invoice.invoice_number,
        )

    def commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        try:
            self._commit_automatic_step(command)
            self._session.commit()
        except BaseException:
            self._session.rollback()
            raise

    def _commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        if command.next_state_version != command.expected_state_version + 1:
            raise StepStateError("Automatic step must advance state_version by one")
        run = self._session.get(InvoiceWorkflowRun, command.run_id)
        cursor = self._session.get(ExecutionCursor, command.run_id)
        if run is None or cursor is None:
            raise ReadyStepNotFound(f"Run {command.run_id!r} does not exist")
        if (
            cursor.phase != "READY"
            or cursor.current_task_id != command.task_id
        ):
            raise StepStateError("Automatic step no longer matches the ready cursor")

        task = self._session.get(RevisionTask, command.task_id)
        invoice = self._session.get(Invoice, run.invoice_id)
        if (
            task is None
            or invoice is None
            or task.revision_id != run.revision_id
        ):
            raise StepStateError("Automatic step crosses its run revision boundary")
        completed_attempts = int(
            self._session.scalar(
                select(func.count())
                .select_from(InvoiceTaskAttempt)
                .where(
                    InvoiceTaskAttempt.run_id == run.id,
                    InvoiceTaskAttempt.task_id == task.id,
                )
            )
            or 0
        )
        if command.attempt_ordinal != completed_attempts + 1:
            raise StepStateError("Attempt ordinal is not the next task attempt")

        next_task_id, phase, terminal = self._next_cursor_values(
            run,
            task,
            command,
        )
        cursor_update = self._session.execute(
            update(ExecutionCursor)
            .where(
                ExecutionCursor.run_id == command.run_id,
                ExecutionCursor.state_version == command.expected_state_version,
                ExecutionCursor.phase == "READY",
                ExecutionCursor.current_task_id == command.task_id,
            )
            .values(
                current_task_id=next_task_id,
                phase=phase,
                state_version=command.next_state_version,
                terminal_decision=terminal,
            )
            .execution_options(synchronize_session=False)
        )
        if cursor_update.rowcount != 1:
            raise StateVersionConflict(
                f"Expected state version {command.expected_state_version} "
                f"for run {command.run_id!r}"
            )

        self._session.add(
            InvoiceTaskAttempt(
                run_id=command.run_id,
                task_id=command.task_id,
                attempt_ordinal=command.attempt_ordinal,
                outcome=command.result.outcome.value,
                failure_class=(
                    command.result.failure_class.value
                    if command.result.failure_class is not None
                    else None
                ),
                reason=command.result.reason,
                started_at=command.started_at,
                finished_at=command.finished_at,
            )
        )
        self._apply_effects(invoice, run, command)
        self._append_trace(command)

        if phase == "TERMINAL":
            run.status = (
                "COMPLETED"
                if terminal == TerminalDecision.SUCCESSFUL_TERMINAL.value
                else "FAILED"
            )
            run.finished_at = command.finished_at

    def _next_cursor_values(
        self,
        run: InvoiceWorkflowRun,
        task: RevisionTask,
        command: AutomaticStepCommit,
    ) -> tuple[int | None, str, str | None]:
        resolution = command.resolution
        if isinstance(resolution, RetryCurrentTask):
            if (
                resolution.task_id != task.id
                or resolution.next_attempt_ordinal != command.attempt_ordinal + 1
            ):
                raise StepStateError("Retry resolution does not repeat this task")
            return task.id, "READY", None
        if isinstance(resolution, TransitionSelected):
            selected = resolution.transition
            transition = self._session.get(RevisionTransition, selected.id)
            if (
                transition is None
                or transition.revision_id != run.revision_id
                or transition.from_task_id != task.id
                or selected.from_task_id != task.id
                or transition.to_task_id != selected.to_task_id
                or transition.condition != selected.condition.value
            ):
                raise StepStateError(
                    "Selected transition is not an edge in the run revision"
                )
            return transition.to_task_id, "READY", None
        if isinstance(resolution, TerminalReached):
            return None, "TERMINAL", resolution.decision.value
        raise TypeError("Unsupported automatic step resolution")

    def _apply_effects(
        self,
        invoice: Invoice,
        run: InvoiceWorkflowRun,
        command: AutomaticStepCommit,
    ) -> None:
        for effect in command.effects:
            if isinstance(effect, InvoiceMetadataValidated):
                if command.result.outcome.value != "SUCCESS":
                    raise StepStateError(
                        "Validated metadata requires a successful task result"
                    )
                metadata = effect.metadata
                invoice.supplier_name = metadata.supplier_name
                invoice.invoice_number = metadata.invoice_number
                invoice.issue_date = metadata.issue_date
                invoice.amount = metadata.amount
                invoice.currency = metadata.currency
            elif isinstance(effect, InvoiceStateChanged):
                invoice.state = effect.state.value
            elif isinstance(effect, ArchiveRecordCreated):
                if command.result.outcome.value != "SUCCESS":
                    raise StepStateError(
                        "Archive record requires a successful task result"
                    )
                if effect.document_identity != invoice.document_identity:
                    raise StepStateError(
                        "Archive effect changed the controlled document identity"
                    )
                self._session.add(
                    ArchiveRecord(
                        id=self._id_factory(),
                        invoice_id=invoice.id,
                        run_id=run.id,
                        document_identity=effect.document_identity,
                        archived_at=command.finished_at,
                    )
                )
            elif isinstance(effect, InternalNotificationCreated):
                if command.result.outcome.value != "SUCCESS":
                    raise StepStateError(
                        "Notification requires a successful task result"
                    )
                self._session.add(
                    InternalNotification(
                        id=self._id_factory(),
                        invoice_id=invoice.id,
                        run_id=run.id,
                        message=effect.message,
                        created_at=command.finished_at,
                    )
                )
            else:
                raise TypeError(f"Unsupported automatic step effect {effect!r}")

    def _append_trace(self, command: AutomaticStepCommit) -> None:
        last_position = int(
            self._session.scalar(
                select(func.max(InvoiceTraceEntry.position)).where(
                    InvoiceTraceEntry.run_id == command.run_id
                )
            )
            or 0
        )
        entries: list[InvoiceTraceEntry] = []
        for offset, observation in enumerate(command.trace, start=1):
            if (
                observation.task_id != command.task_id
                or observation.attempt_ordinal != command.attempt_ordinal
            ):
                raise StepStateError("Trace observation does not match its attempt")
            detail = observation.detail
            if observation.transition_id is not None:
                transition_detail = f"transition_id={observation.transition_id}"
                detail = (
                    f"{detail}; {transition_detail}"
                    if detail
                    else transition_detail
                )
            entries.append(
                InvoiceTraceEntry(
                    run_id=command.run_id,
                    position=last_position + offset,
                    observation_kind=observation.kind.value,
                    task_id=observation.task_id,
                    attempt_ordinal=observation.attempt_ordinal,
                    detail=detail,
                    timestamp=command.finished_at,
                )
            )
        self._session.add_all(entries)
