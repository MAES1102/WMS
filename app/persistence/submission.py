"""Atomic persistence for initial Purchase Request submission."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.submission import ActiveWorkflow, CreateSubmission, SubmissionConflict, SubmissionUnavailable
from app.persistence.models import ExecutionCursor, PurchaseRequest, PurchaseRequestTraceEntry, PurchaseRequestWorkflowRun, RevisionTask, WorkflowRevision


class ActiveWorkflowNotFound(SubmissionUnavailable): pass


class SqlAlchemySubmissionUnitOfWork:
    def __init__(self, session: Session) -> None:
        self._session = session

    def load_active_workflow(self) -> ActiveWorkflow:
        revision = self._session.scalars(select(WorkflowRevision).order_by(WorkflowRevision.activated_at.desc(), WorkflowRevision.id.desc())).first()
        if revision is None:
            raise ActiveWorkflowNotFound("No active workflow revision exists")
        starts = self._session.scalars(select(RevisionTask).where(RevisionTask.revision_id == revision.id, RevisionTask.is_start.is_(True))).all()
        if len(starts) != 1:
            raise ActiveWorkflowNotFound(f"Revision {revision.id} must have exactly one start task")
        return ActiveWorkflow(revision.id, starts[0].id)

    def create_submission(self, command: CreateSubmission) -> None:
        raw = command.request
        request = PurchaseRequest(
            id=command.purchase_request_id, requester_name_raw=raw.requester_name,
            department_raw=raw.department, item_or_service_raw=raw.item_or_service,
            supplier_raw=raw.supplier, amount_raw=raw.amount, currency_raw=raw.currency,
            business_justification_raw=raw.business_justification,
            required_date_raw=raw.required_date, requester_name=None, department=None,
            item_or_service=None, supplier=None, amount=None, currency=None,
            business_justification=None, required_date=None, state="SUBMITTED",
            created_at=command.submitted_at,
        )
        run = PurchaseRequestWorkflowRun(
            id=command.run_id, purchase_request_id=command.purchase_request_id,
            revision_id=command.revision_id, mode=command.mode.value,
            scenario=command.scenario.value, status="RUNNING",
            started_at=command.submitted_at, finished_at=None,
        )
        cursor = ExecutionCursor(run_id=command.run_id, current_task_id=command.start_task_id, phase="READY", state_version=1, terminal_decision=None)
        trace = PurchaseRequestTraceEntry(
            run_id=command.run_id, position=1, observation_kind="RUN_STARTED",
            task_id=command.start_task_id, attempt_ordinal=None,
            detail=f"purchase_request_id={command.purchase_request_id}; mode={command.mode.value}; scenario={command.scenario.value}",
            timestamp=command.submitted_at,
        )
        try:
            self._session.add(request)
            self._session.flush()
            self._session.add(run)
            self._session.flush()
            self._session.add_all((cursor, trace))
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise SubmissionConflict("Purchase Request submission conflicts with persisted state") from exc
        except BaseException:
            self._session.rollback()
            raise
