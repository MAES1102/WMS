"""SQLAlchemy transaction adapter for initial v3 invoice submission."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.submission import (
    ActiveWorkflow,
    CreateSubmission,
    SubmissionConflict,
    SubmissionUnavailable,
)
from app.persistence.models import (
    ExecutionCursor,
    Invoice,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
    WorkflowRevision,
)


class ActiveWorkflowNotFound(SubmissionUnavailable):
    pass


class SqlAlchemySubmissionUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session

    def load_active_workflow(self) -> ActiveWorkflow:
        revision = self._session.scalars(
            select(WorkflowRevision).order_by(
                WorkflowRevision.activated_at.desc(),
                WorkflowRevision.id.desc(),
            )
        ).first()
        if revision is None:
            raise ActiveWorkflowNotFound("No active workflow revision exists")
        start_tasks = self._session.scalars(
            select(RevisionTask).where(
                RevisionTask.revision_id == revision.id,
                RevisionTask.is_start.is_(True),
            )
        ).all()
        if len(start_tasks) != 1:
            raise ActiveWorkflowNotFound(
                f"Revision {revision.id} must have exactly one start task"
            )
        return ActiveWorkflow(revision.id, start_tasks[0].id)

    def create_submission(self, command: CreateSubmission) -> None:
        metadata = command.metadata
        invoice = Invoice(
            id=command.invoice_id,
            supplier_name_raw=metadata.supplier_name,
            invoice_number_raw=metadata.invoice_number,
            issue_date_raw=metadata.issue_date,
            amount_raw=metadata.amount,
            currency_raw=metadata.currency,
            supplier_name=None,
            invoice_number=None,
            issue_date=None,
            amount=None,
            currency=None,
            document_identity=command.document_identity,
            original_filename=command.original_filename,
            declared_media_type=command.declared_media_type,
            document_size_bytes=command.document_size_bytes,
            state="SUBMITTED",
            created_at=command.created_at,
        )
        run = InvoiceWorkflowRun(
            id=command.run_id,
            invoice_id=command.invoice_id,
            revision_id=command.revision_id,
            mode=command.mode.value,
            status="RUNNING",
            started_at=command.created_at,
            finished_at=None,
        )
        cursor = ExecutionCursor(
            run_id=command.run_id,
            current_task_id=command.start_task_id,
            phase="READY",
            state_version=1,
            terminal_decision=None,
        )
        trace = InvoiceTraceEntry(
            run_id=command.run_id,
            position=1,
            observation_kind="RUN_STARTED",
            task_id=command.start_task_id,
            attempt_ordinal=None,
            detail=f"invoice_id={command.invoice_id}; mode={command.mode.value}",
            timestamp=command.created_at,
        )
        try:
            self._session.add(invoice)
            self._session.flush()
            self._session.add(run)
            self._session.flush()
            self._session.add_all((cursor, trace))
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise SubmissionConflict(
                "Invoice submission conflicts with persisted state"
            ) from exc
        except BaseException:
            self._session.rollback()
            raise
