"""SQLAlchemy control-state and status projections for purchase_request orchestration."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.errors import StepStateError
from app.application.orchestration import (
    ApprovalResultView,
    CursorPhase,
    PurchaseRequestRunNotFound,
    PurchaseRequestRunStatusView,
    PurchaseRequestTraceView,
    RunControlState,
)
from app.domain.types import DemoScenario, ExecutionMode, TaskType, TerminalDecision
from app.persistence.models import (
    ApprovalDecision,
    ApprovalWorkItem,
    PurchaseAuthorization,
    ExecutionCursor,
    InternalNotification,
    PurchaseRequest,
    PurchaseRequestTraceEntry,
    PurchaseRequestWorkflowRun,
    RevisionTask,
)


class SqlAlchemyRunControlReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def load_control_state(self, run_id: str) -> RunControlState:
        run = self._session.get(PurchaseRequestWorkflowRun, run_id)
        cursor = self._session.get(ExecutionCursor, run_id)
        if run is None or cursor is None:
            raise PurchaseRequestRunNotFound(f"Run {run_id!r} does not exist")

        phase = CursorPhase(cursor.phase)
        task_type: TaskType | None = None
        if cursor.current_task_id is not None:
            task = self._session.get(RevisionTask, cursor.current_task_id)
            if task is None or task.revision_id != run.revision_id:
                raise StepStateError(
                    "Execution cursor task is outside the run revision"
                )
            task_type = TaskType(task.task_type)

        work_item_id: str | None = None
        if phase is CursorPhase.WAITING_FOR_APPROVAL:
            item = self._session.scalars(
                select(ApprovalWorkItem).where(
                    ApprovalWorkItem.run_id == run.id,
                    ApprovalWorkItem.task_id == cursor.current_task_id,
                    ApprovalWorkItem.state == "PENDING",
                )
            ).one_or_none()
            if item is None:
                raise StepStateError(
                    "Waiting cursor has no matching pending approval item"
                )
            work_item_id = item.id

        return RunControlState(
            run_id=run.id,
            mode=ExecutionMode(run.mode),
            phase=phase,
            state_version=cursor.state_version,
            task_type=task_type,
            work_item_id=work_item_id,
            terminal_decision=(
                TerminalDecision(cursor.terminal_decision)
                if cursor.terminal_decision is not None
                else None
            ),
        )


class SqlAlchemyPurchaseRequestRunQueryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, run_id: str) -> PurchaseRequestRunStatusView:
        run = self._session.get(PurchaseRequestWorkflowRun, run_id)
        cursor = self._session.get(ExecutionCursor, run_id)
        if run is None or cursor is None:
            raise PurchaseRequestRunNotFound(f"Run {run_id!r} does not exist")
        purchase_request = self._session.get(PurchaseRequest, run.purchase_request_id)
        if purchase_request is None:
            raise StepStateError("Run has no purchase_request")

        item = self._session.scalars(
            select(ApprovalWorkItem).where(ApprovalWorkItem.run_id == run.id)
        ).one_or_none()
        approval: ApprovalResultView | None = None
        if item is not None:
            decision = self._session.scalars(
                select(ApprovalDecision).where(
                    ApprovalDecision.work_item_id == item.id
                )
            ).one_or_none()
            if decision is not None:
                approval = ApprovalResultView(
                    decision=decision.decision,
                    note=decision.note,
                    reason=decision.reason,
                    decided_at=decision.decided_at,
                )

        authorization = self._session.scalars(
            select(PurchaseAuthorization).where(PurchaseAuthorization.run_id == run.id)
        ).one_or_none()
        notification = self._session.scalars(
            select(InternalNotification).where(
                InternalNotification.run_id == run.id
            )
        ).one_or_none()
        trace_rows = self._session.scalars(
            select(PurchaseRequestTraceEntry)
            .where(PurchaseRequestTraceEntry.run_id == run.id)
            .order_by(PurchaseRequestTraceEntry.position)
        ).all()

        return PurchaseRequestRunStatusView(
            purchase_request_id=purchase_request.id,
            requester_name=purchase_request.requester_name or purchase_request.requester_name_raw.strip(),
            department=purchase_request.department or purchase_request.department_raw.strip(),
            item_or_service=purchase_request.item_or_service or purchase_request.item_or_service_raw.strip(),
            supplier=purchase_request.supplier or purchase_request.supplier_raw.strip(),
            amount=format(purchase_request.amount, "f") if purchase_request.amount is not None else purchase_request.amount_raw,
            currency=purchase_request.currency or purchase_request.currency_raw,
            business_justification=purchase_request.business_justification or purchase_request.business_justification_raw,
            required_date=purchase_request.required_date.isoformat() if purchase_request.required_date is not None else purchase_request.required_date_raw,
            run_id=run.id,
            execution_mode=ExecutionMode(run.mode),
            scenario=DemoScenario(run.scenario),
            purchase_request_state=purchase_request.state,
            run_status=run.status,
            cursor_phase=CursorPhase(cursor.phase),
            state_version=cursor.state_version,
            terminal_decision=(
                TerminalDecision(cursor.terminal_decision)
                if cursor.terminal_decision is not None
                else None
            ),
            approval=approval,
            purchase_authorization_code=(
                authorization.authorization_code if authorization is not None else None
            ),
            notification=(
                notification.message if notification is not None else None
            ),
            trace=tuple(
                PurchaseRequestTraceView(
                    position=row.position,
                    kind=row.observation_kind,
                    task_id=row.task_id,
                    attempt_ordinal=row.attempt_ordinal,
                    detail=row.detail,
                    timestamp=row.timestamp,
                )
                for row in trace_rows
            ),
        )
