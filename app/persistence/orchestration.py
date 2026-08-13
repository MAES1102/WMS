"""SQLAlchemy control-state and status projections for invoice orchestration."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.errors import StepStateError
from app.application.orchestration import (
    ApprovalResultView,
    CursorPhase,
    InvoiceRunNotFound,
    InvoiceRunStatusView,
    InvoiceTraceView,
    RunControlState,
)
from app.domain.types import ExecutionMode, TaskType, TerminalDecision
from app.persistence.models import (
    ApprovalDecision,
    ApprovalWorkItem,
    ArchiveRecord,
    ExecutionCursor,
    InternalNotification,
    Invoice,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
)


class SqlAlchemyRunControlReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def load_control_state(self, run_id: str) -> RunControlState:
        run = self._session.get(InvoiceWorkflowRun, run_id)
        cursor = self._session.get(ExecutionCursor, run_id)
        if run is None or cursor is None:
            raise InvoiceRunNotFound(f"Run {run_id!r} does not exist")

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


class SqlAlchemyInvoiceRunQueryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, run_id: str) -> InvoiceRunStatusView:
        run = self._session.get(InvoiceWorkflowRun, run_id)
        cursor = self._session.get(ExecutionCursor, run_id)
        if run is None or cursor is None:
            raise InvoiceRunNotFound(f"Run {run_id!r} does not exist")
        invoice = self._session.get(Invoice, run.invoice_id)
        if invoice is None:
            raise StepStateError("Run has no invoice")

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

        archive = self._session.scalars(
            select(ArchiveRecord).where(ArchiveRecord.run_id == run.id)
        ).one_or_none()
        notification = self._session.scalars(
            select(InternalNotification).where(
                InternalNotification.run_id == run.id
            )
        ).one_or_none()
        trace_rows = self._session.scalars(
            select(InvoiceTraceEntry)
            .where(InvoiceTraceEntry.run_id == run.id)
            .order_by(InvoiceTraceEntry.position)
        ).all()

        return InvoiceRunStatusView(
            invoice_id=invoice.id,
            supplier_name=(
                invoice.supplier_name
                or invoice.supplier_name_raw.strip()
                or "Unknown supplier"
            ),
            invoice_number=(
                invoice.invoice_number
                or invoice.invoice_number_raw.strip()
                or invoice.id
            ),
            run_id=run.id,
            execution_mode=ExecutionMode(run.mode),
            invoice_state=invoice.state,
            run_status=run.status,
            cursor_phase=CursorPhase(cursor.phase),
            state_version=cursor.state_version,
            terminal_decision=(
                TerminalDecision(cursor.terminal_decision)
                if cursor.terminal_decision is not None
                else None
            ),
            approval=approval,
            archive_document_identity=(
                archive.document_identity if archive is not None else None
            ),
            notification=(
                notification.message if notification is not None else None
            ),
            trace=tuple(
                InvoiceTraceView(
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
