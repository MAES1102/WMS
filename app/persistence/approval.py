"""SQLAlchemy adapter for persistent human approval and same-run resume."""

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.approval import (
    ApprovalNotFound,
    ApprovalTraceObservation,
    ApprovalWorkItemView,
    CommitApprovalDecisionCommand,
    EnterApprovalWaitCommand,
    ExistingApprovalDecision,
    PendingApprovalDecision,
    ReadyHumanApproval,
    WaitingHumanApproval,
)
from app.application.errors import StateVersionConflict, StepStateError
from app.domain.approval import (
    ApprovalChoice,
    ValidatedApprovalDecision,
)
from app.domain.types import (
    TaskDefinition,
    TaskOutcome,
    TaskType,
    TerminalDecision,
    TerminalReached,
    TransitionCondition,
    TransitionDefinition,
    TransitionSelected,
)
from app.persistence.models import (
    ApprovalDecision as ApprovalDecisionRow,
    ApprovalWorkItem,
    ExecutionCursor,
    Invoice,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
    RevisionTransition,
)


class ApprovalStateNotFound(ApprovalNotFound):
    pass


class SqlAlchemyApprovalUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session

    def load_human_approval(
        self,
        run_id: str,
    ) -> ReadyHumanApproval | WaitingHumanApproval:
        run, cursor, task = self._load_run_cursor_task(run_id)
        if cursor.phase == "READY":
            return ReadyHumanApproval(
                run_id=run.id,
                invoice_id=run.invoice_id,
                task=self._task_definition(task),
                transitions=self._transitions(run.revision_id, task.id),
                state_version=cursor.state_version,
            )
        if cursor.phase == "WAITING_FOR_APPROVAL":
            item = self._session.scalars(
                select(ApprovalWorkItem).where(
                    ApprovalWorkItem.run_id == run.id,
                    ApprovalWorkItem.task_id == task.id,
                )
            ).one_or_none()
            if item is None or item.state != "PENDING":
                raise StepStateError(
                    "Waiting cursor has no matching pending approval item"
                )
            return WaitingHumanApproval(
                run_id=run.id,
                invoice_id=run.invoice_id,
                task_id=task.id,
                work_item_id=item.id,
                state_version=cursor.state_version,
            )
        raise StepStateError(f"Run {run_id!r} is terminal, not approvable")

    def commit_wait(self, command: EnterApprovalWaitCommand) -> None:
        try:
            self._commit_wait(command)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise StateVersionConflict(
                "Approval work item or waiting state was concurrently created"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise

    def _commit_wait(self, command: EnterApprovalWaitCommand) -> None:
        self._check_version_increment(
            command.expected_state_version,
            command.next_state_version,
        )
        run, cursor, task = self._load_run_cursor_task(command.run_id)
        invoice = self._session.get(Invoice, command.invoice_id)
        if (
            invoice is None
            or run.invoice_id != invoice.id
            or task.id != command.task_id
            or task.task_type != TaskType.HUMAN_APPROVAL.value
        ):
            raise StepStateError("Waiting command crosses its run/task boundary")

        changed = self._session.execute(
            update(ExecutionCursor)
            .where(
                ExecutionCursor.run_id == command.run_id,
                ExecutionCursor.state_version == command.expected_state_version,
                ExecutionCursor.phase == "READY",
                ExecutionCursor.current_task_id == command.task_id,
            )
            .values(
                phase="WAITING_FOR_APPROVAL",
                state_version=command.next_state_version,
                terminal_decision=None,
            )
            .execution_options(synchronize_session=False)
        )
        if changed.rowcount != 1:
            raise StateVersionConflict(
                f"Expected ready version {command.expected_state_version}"
            )

        run.status = "WAITING_FOR_APPROVAL"
        invoice.state = "PENDING_APPROVAL"
        self._session.add(
            ApprovalWorkItem(
                id=command.work_item_id,
                run_id=run.id,
                invoice_id=invoice.id,
                task_id=task.id,
                state="PENDING",
                created_at=command.created_at,
                decided_at=None,
            )
        )
        self._append_trace(
            command.run_id,
            command.trace,
            command.created_at,
        )

    def load_approval_decision(
        self,
        work_item_id: str,
    ) -> PendingApprovalDecision | ExistingApprovalDecision:
        item = self._session.get(ApprovalWorkItem, work_item_id)
        if item is None:
            raise ApprovalStateNotFound(
                f"Approval work item {work_item_id!r} does not exist"
            )
        run, cursor, task = self._load_run_cursor_task(
            item.run_id,
            task_id=item.task_id,
        )
        decision_row = self._session.scalars(
            select(ApprovalDecisionRow).where(
                ApprovalDecisionRow.work_item_id == item.id
            )
        ).one_or_none()
        if decision_row is not None:
            choice = ApprovalChoice(decision_row.decision)
            return ExistingApprovalDecision(
                run_id=run.id,
                work_item_id=item.id,
                decision=ValidatedApprovalDecision(
                    choice=choice,
                    note=decision_row.note,
                    reason=decision_row.reason,
                ),
                outcome=(
                    TaskOutcome.SUCCESS
                    if choice is ApprovalChoice.APPROVE
                    else TaskOutcome.FAILURE
                ),
                state_version=cursor.state_version,
            )
        if (
            item.state != "PENDING"
            or cursor.phase != "WAITING_FOR_APPROVAL"
            or cursor.current_task_id != item.task_id
        ):
            raise StepStateError(
                "Pending approval item does not match the waiting cursor"
            )
        return PendingApprovalDecision(
            run_id=run.id,
            invoice_id=run.invoice_id,
            task=self._task_definition(task),
            transitions=self._transitions(run.revision_id, task.id),
            work_item_id=item.id,
            state_version=cursor.state_version,
        )

    def commit_decision(self, command: CommitApprovalDecisionCommand) -> None:
        try:
            self._commit_decision(command)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise StateVersionConflict(
                "Approval decision or cursor was concurrently committed"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise

    def _commit_decision(self, command: CommitApprovalDecisionCommand) -> None:
        self._check_version_increment(
            command.expected_state_version,
            command.next_state_version,
        )
        item = self._session.get(ApprovalWorkItem, command.work_item_id)
        run, cursor, task = self._load_run_cursor_task(
            command.run_id,
            task_id=command.task_id,
        )
        invoice = self._session.get(Invoice, command.invoice_id)
        if (
            item is None
            or invoice is None
            or item.state != "PENDING"
            or item.run_id != run.id
            or item.invoice_id != invoice.id
            or item.task_id != task.id
            or run.invoice_id != invoice.id
        ):
            raise StepStateError("Decision command crosses its work-item boundary")

        next_task_id, phase, terminal = self._next_cursor_values(
            run,
            task,
            command,
        )
        changed = self._session.execute(
            update(ExecutionCursor)
            .where(
                ExecutionCursor.run_id == command.run_id,
                ExecutionCursor.state_version == command.expected_state_version,
                ExecutionCursor.phase == "WAITING_FOR_APPROVAL",
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
        if changed.rowcount != 1:
            raise StateVersionConflict(
                f"Expected waiting version {command.expected_state_version}"
            )

        item.state = (
            "APPROVED"
            if command.decision.choice is ApprovalChoice.APPROVE
            else "REJECTED"
        )
        item.decided_at = command.decided_at
        invoice.state = command.invoice_state.value
        self._session.add(
            ApprovalDecisionRow(
                id=command.decision_id,
                work_item_id=item.id,
                decision=command.decision.choice.value,
                note=command.decision.note,
                reason=command.decision.reason,
                decided_at=command.decided_at,
            )
        )
        if phase == "TERMINAL":
            run.status = (
                "COMPLETED"
                if terminal == TerminalDecision.SUCCESSFUL_TERMINAL.value
                else "FAILED"
            )
            run.finished_at = command.decided_at
        else:
            run.status = "RUNNING"
        self._append_trace(
            command.run_id,
            command.trace,
            command.decided_at,
        )

    def _load_run_cursor_task(
        self,
        run_id: str,
        *,
        task_id: int | None = None,
    ) -> tuple[InvoiceWorkflowRun, ExecutionCursor, RevisionTask]:
        run = self._session.get(InvoiceWorkflowRun, run_id)
        cursor = self._session.get(ExecutionCursor, run_id)
        selected_task_id = task_id or (cursor.current_task_id if cursor else None)
        task = (
            self._session.get(RevisionTask, selected_task_id)
            if selected_task_id is not None
            else None
        )
        if run is None or cursor is None or task is None:
            raise ApprovalStateNotFound(
                f"Run {run_id!r} has no complete approval state"
            )
        if task.revision_id != run.revision_id:
            raise StepStateError("Approval task is outside the run revision")
        return run, cursor, task

    def _transitions(
        self,
        revision_id: int,
        task_id: int,
    ) -> tuple[TransitionDefinition, ...]:
        rows = self._session.scalars(
            select(RevisionTransition)
            .where(
                RevisionTransition.revision_id == revision_id,
                RevisionTransition.from_task_id == task_id,
            )
            .order_by(RevisionTransition.id)
        ).all()
        return tuple(
            TransitionDefinition(
                id=row.id,
                from_task_id=row.from_task_id,
                to_task_id=row.to_task_id,
                condition=TransitionCondition(row.condition),
            )
            for row in rows
        )

    @staticmethod
    def _task_definition(task: RevisionTask) -> TaskDefinition:
        return TaskDefinition(
            id=task.id,
            name=task.name,
            task_type=TaskType(task.task_type),
            is_start=task.is_start,
            max_attempts=task.max_attempts,
        )

    def _next_cursor_values(
        self,
        run: InvoiceWorkflowRun,
        task: RevisionTask,
        command: CommitApprovalDecisionCommand,
    ) -> tuple[int | None, str, str | None]:
        resolution = command.resolution
        if isinstance(resolution, TransitionSelected):
            selected = resolution.transition
            row = self._session.get(RevisionTransition, selected.id)
            if (
                row is None
                or row.revision_id != run.revision_id
                or row.from_task_id != task.id
                or selected.from_task_id != task.id
                or row.to_task_id != selected.to_task_id
                or row.condition != selected.condition.value
            ):
                raise StepStateError(
                    "Approval selected a transition outside the run revision"
                )
            return row.to_task_id, "READY", None
        if isinstance(resolution, TerminalReached):
            return None, "TERMINAL", resolution.decision.value
        raise TypeError("Unsupported approval resolution")

    def _append_trace(
        self,
        run_id: str,
        observations: tuple[ApprovalTraceObservation, ...],
        timestamp,
    ) -> None:
        last_position = int(
            self._session.scalar(
                select(func.max(InvoiceTraceEntry.position)).where(
                    InvoiceTraceEntry.run_id == run_id
                )
            )
            or 0
        )
        rows: list[InvoiceTraceEntry] = []
        for offset, observation in enumerate(observations, start=1):
            detail = observation.detail
            if observation.transition_id is not None:
                transition_detail = f"transition_id={observation.transition_id}"
                detail = (
                    f"{detail}; {transition_detail}"
                    if detail
                    else transition_detail
                )
            rows.append(
                InvoiceTraceEntry(
                    run_id=run_id,
                    position=last_position + offset,
                    observation_kind=observation.kind.value,
                    task_id=observation.task_id,
                    attempt_ordinal=None,
                    detail=detail,
                    timestamp=timestamp,
                )
            )
        self._session.add_all(rows)

    @staticmethod
    def _check_version_increment(expected: int, following: int) -> None:
        if following != expected + 1:
            raise StepStateError("Approval step must advance state_version by one")


class SqlAlchemyApprovalQueryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_pending(self) -> tuple[ApprovalWorkItemView, ...]:
        items = self._session.scalars(
            select(ApprovalWorkItem)
            .where(ApprovalWorkItem.state == "PENDING")
            .order_by(ApprovalWorkItem.created_at, ApprovalWorkItem.id)
        ).all()
        return tuple(self._view(item) for item in items)

    def get(self, work_item_id: str) -> ApprovalWorkItemView:
        item = self._session.get(ApprovalWorkItem, work_item_id)
        if item is None:
            raise ApprovalStateNotFound(
                f"Approval work item {work_item_id!r} does not exist"
            )
        return self._view(item)

    def _view(self, item: ApprovalWorkItem) -> ApprovalWorkItemView:
        invoice = self._session.get(Invoice, item.invoice_id)
        run = self._session.get(InvoiceWorkflowRun, item.run_id)
        cursor = self._session.get(ExecutionCursor, item.run_id)
        if invoice is None or run is None or cursor is None:
            raise StepStateError("Approval item has incomplete invoice/run context")
        return ApprovalWorkItemView(
            work_item_id=item.id,
            run_id=run.id,
            invoice_id=invoice.id,
            supplier_name=invoice.supplier_name,
            invoice_number=invoice.invoice_number,
            issue_date=(
                invoice.issue_date.isoformat()
                if invoice.issue_date is not None
                else invoice.issue_date_raw
            ),
            amount=(
                format(invoice.amount, "f")
                if invoice.amount is not None
                else invoice.amount_raw
            ),
            currency=invoice.currency or invoice.currency_raw,
            document_identity=invoice.document_identity,
            approval_state=item.state,
            invoice_state=invoice.state,
            run_status=run.status,
            state_version=cursor.state_version,
            created_at=item.created_at,
        )
