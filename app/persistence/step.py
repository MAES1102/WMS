"""SQLAlchemy adapter for one atomic automatic workflow step."""

from collections.abc import Callable
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.errors import StateVersionConflict, StepStateError
from app.application.purchase_request_validation import (
    PurchaseRequestValidationInput,
)
from app.application.purchase_request_tasks import PurchaseRequestBusinessSnapshot
from app.application.ports import (
    PurchaseAuthorizationCreated,
    AutomaticStepCommit,
    ExecutionContext,
    InternalNotificationCreated,
    PurchaseRequestValidated,
    PurchaseRequestStateChanged,
    ReadyAutomaticStep,
    RetryCurrentTask,
)
from app.domain.purchase_request import PurchaseRequestState, RawPurchaseRequest
from app.domain.types import (
    TerminalDecision,
    TerminalReached,
    TransitionSelected,
)
from app.persistence._shared import (
    apply_version_gated_cursor_update,
    build_task_definition,
    format_trace_detail,
    next_trace_position,
    query_transitions,
)
from app.persistence.models import (
    PurchaseAuthorization,
    ExecutionCursor,
    PurchaseRequest,
    PurchaseRequestTaskAttempt,
    PurchaseRequestTraceEntry,
    PurchaseRequestWorkflowRun,
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
        run = self._session.get(PurchaseRequestWorkflowRun, run_id)
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
        completed_attempts = self._session.scalar(
            select(func.count())
            .select_from(PurchaseRequestTaskAttempt)
            .where(
                PurchaseRequestTaskAttempt.run_id == run.id,
                PurchaseRequestTaskAttempt.task_id == task.id,
            )
        )
        return ReadyAutomaticStep(
            run_id=run.id,
            purchase_request_id=run.purchase_request_id,
            task=build_task_definition(task),
            transitions=query_transitions(self._session, run.revision_id, task.id),
            completed_attempts=int(completed_attempts or 0),
            state_version=cursor.state_version,
        )

    def load(self, context: ExecutionContext) -> PurchaseRequestValidationInput:
        run = self._session.get(PurchaseRequestWorkflowRun, context.run_id)
        purchase_request = self._session.get(PurchaseRequest, context.purchase_request_id)
        if run is None or purchase_request is None or run.purchase_request_id != purchase_request.id:
            raise ReadyStepNotFound(
                "Validation context does not identify one persisted purchase_request run"
            )
        cursor = self._session.get(ExecutionCursor, context.run_id)
        if cursor is None or cursor.current_task_id != context.task_id:
            raise StepStateError("Validation context is not the current cursor task")
        return PurchaseRequestValidationInput(
            request=RawPurchaseRequest(
                requester_name=purchase_request.requester_name_raw,
                department=purchase_request.department_raw,
                item_or_service=purchase_request.item_or_service_raw,
                supplier=purchase_request.supplier_raw,
                amount=purchase_request.amount_raw,
                currency=purchase_request.currency_raw,
                business_justification=purchase_request.business_justification_raw,
                required_date=purchase_request.required_date_raw,
            ),
            submitted_on=purchase_request.created_at.date(),
        )

    def load_business(self, context: ExecutionContext) -> PurchaseRequestBusinessSnapshot:
        run = self._session.get(PurchaseRequestWorkflowRun, context.run_id)
        purchase_request = self._session.get(PurchaseRequest, context.purchase_request_id)
        cursor = self._session.get(ExecutionCursor, context.run_id)
        if (
            run is None
            or purchase_request is None
            or cursor is None
            or run.purchase_request_id != purchase_request.id
            or cursor.phase != "READY"
            or cursor.current_task_id != context.task_id
        ):
            raise StepStateError(
                "Business task context does not match one ready purchase_request run"
            )
        return PurchaseRequestBusinessSnapshot(
            state=PurchaseRequestState(purchase_request.state),
            item_or_service=purchase_request.item_or_service,
            amount=format(purchase_request.amount, "f") if purchase_request.amount is not None else purchase_request.amount_raw,
            currency=purchase_request.currency or purchase_request.currency_raw,
        )

    def commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        try:
            self._commit_automatic_step(command)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise StateVersionConflict(
                "Automatic step attempt or cursor was concurrently committed"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise

    def _commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        if command.next_state_version != command.expected_state_version + 1:
            raise StepStateError("Automatic step must advance state_version by one")
        run = self._session.get(PurchaseRequestWorkflowRun, command.run_id)
        cursor = self._session.get(ExecutionCursor, command.run_id)
        if run is None or cursor is None:
            raise ReadyStepNotFound(f"Run {command.run_id!r} does not exist")
        if (
            cursor.phase != "READY"
            or cursor.current_task_id != command.task_id
        ):
            raise StepStateError("Automatic step no longer matches the ready cursor")

        task = self._session.get(RevisionTask, command.task_id)
        purchase_request = self._session.get(PurchaseRequest, run.purchase_request_id)
        if (
            task is None
            or purchase_request is None
            or task.revision_id != run.revision_id
        ):
            raise StepStateError("Automatic step crosses its run revision boundary")
        completed_attempts = int(
            self._session.scalar(
                select(func.count())
                .select_from(PurchaseRequestTaskAttempt)
                .where(
                    PurchaseRequestTaskAttempt.run_id == run.id,
                    PurchaseRequestTaskAttempt.task_id == task.id,
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
        apply_version_gated_cursor_update(
            self._session,
            run_id=command.run_id,
            expected_version=command.expected_state_version,
            required_phase="READY",
            required_task_id=command.task_id,
            values={
                "current_task_id": next_task_id,
                "phase": phase,
                "state_version": command.next_state_version,
                "terminal_decision": terminal,
            },
            conflict_message=(
                f"Expected state version {command.expected_state_version} "
                f"for run {command.run_id!r}"
            ),
        )

        self._session.add(
            PurchaseRequestTaskAttempt(
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
        self._apply_effects(purchase_request, run, command)
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
        run: PurchaseRequestWorkflowRun,
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
        purchase_request: PurchaseRequest,
        run: PurchaseRequestWorkflowRun,
        command: AutomaticStepCommit,
    ) -> None:
        for effect in command.effects:
            if isinstance(effect, PurchaseRequestValidated):
                if command.result.outcome.value != "SUCCESS":
                    raise StepStateError(
                        "Validated metadata requires a successful task result"
                    )
                value = effect.request
                purchase_request.requester_name = value.requester_name
                purchase_request.department = value.department
                purchase_request.item_or_service = value.item_or_service
                purchase_request.supplier = value.supplier
                purchase_request.amount = value.amount
                purchase_request.currency = value.currency
                purchase_request.business_justification = value.business_justification
                purchase_request.required_date = value.required_date
            elif isinstance(effect, PurchaseRequestStateChanged):
                purchase_request.state = effect.state.value
            elif isinstance(effect, PurchaseAuthorizationCreated):
                if command.result.outcome.value != "SUCCESS":
                    raise StepStateError(
                        "Authorization record requires a successful task result"
                    )
                self._session.add(
                    PurchaseAuthorization(
                        id=self._id_factory(),
                        purchase_request_id=purchase_request.id,
                        run_id=run.id,
                        authorization_code=effect.authorization_id,
                        authorized_at=command.finished_at,
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
                        purchase_request_id=purchase_request.id,
                        run_id=run.id,
                        message=effect.message,
                        created_at=command.finished_at,
                    )
                )
            else:
                raise TypeError(f"Unsupported automatic step effect {effect!r}")

    def _append_trace(self, command: AutomaticStepCommit) -> None:
        last_position = next_trace_position(self._session, command.run_id)
        entries: list[PurchaseRequestTraceEntry] = []
        for offset, observation in enumerate(command.trace, start=1):
            if (
                observation.task_id != command.task_id
                or observation.attempt_ordinal != command.attempt_ordinal
            ):
                raise StepStateError("Trace observation does not match its attempt")
            entries.append(
                PurchaseRequestTraceEntry(
                    run_id=command.run_id,
                    position=last_position + offset,
                    observation_kind=observation.kind.value,
                    task_id=observation.task_id,
                    attempt_ordinal=observation.attempt_ordinal,
                    detail=format_trace_detail(observation.detail, observation.transition_id),
                    timestamp=command.finished_at,
                )
            )
        self._session.add_all(entries)
