from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfWriter
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.application.executors import AutomaticExecutorRegistry
from app.application.invoice_validation import (
    DocumentValidationEffectPolicy,
    DocumentValidationExecutor,
)
from app.application.ports import AutomaticStepCommit, ExecutionContext
from app.application.step_service import (
    AutomaticStepService,
    StateVersionConflict,
)
from app.application.submission import (
    InvoiceSubmission,
    InvoiceSubmissionService,
)
from app.domain.invoice import RawInvoiceMetadata
from app.domain.types import ExecutionMode, TaskOutcome, TaskResult, TaskType
from app.infrastructure.documents import LocalDocumentStorage
from app.infrastructure.pdf import PypdfInspector
from app.persistence.models import (
    ApprovalWorkItem,
    ExecutionCursor,
    Invoice,
    InvoiceTaskAttempt,
    InvoiceTraceEntry,
    RevisionTask,
    RevisionTransition,
    WorkflowDraft,
    WorkflowRevision,
)
from app.persistence.step import SqlAlchemyAutomaticStepUnitOfWork
from app.persistence.submission import SqlAlchemySubmissionUnitOfWork


class SuccessfulExecutor:
    def execute(self, _context: ExecutionContext) -> TaskResult:
        return TaskResult(TaskOutcome.SUCCESS)


class TickingClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 13, 12, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(milliseconds=1)
        return value


class CapturingUnitOfWork:
    def __init__(self, delegate: SqlAlchemyAutomaticStepUnitOfWork) -> None:
        self._delegate = delegate
        self.command: AutomaticStepCommit | None = None

    def load_ready_step(self, run_id: str):
        return self._delegate.load_ready_step(run_id)

    def commit_automatic_step(self, command: AutomaticStepCommit) -> None:
        self.command = command


def one_page_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def create_validation_revision(
    db: Session,
) -> tuple[RevisionTask, RevisionTask, RevisionTask]:
    now = datetime(2026, 8, 13, tzinfo=UTC)
    draft = WorkflowDraft(name="Invoice approval", created_at=now, updated_at=now)
    db.add(draft)
    db.flush()
    revision = WorkflowRevision(
        draft_id=draft.id,
        revision_number=1,
        name=draft.name,
        activated_at=now,
    )
    db.add(revision)
    db.flush()
    validate = RevisionTask(
        revision_id=revision.id,
        task_key="validate",
        name="Validate invoice",
        task_type=TaskType.DOCUMENT_VALIDATION.value,
        is_start=True,
        max_attempts=1,
    )
    approve = RevisionTask(
        revision_id=revision.id,
        task_key="approve",
        name="Review invoice",
        task_type=TaskType.HUMAN_APPROVAL.value,
        is_start=False,
        max_attempts=None,
    )
    notify = RevisionTask(
        revision_id=revision.id,
        task_key="notify",
        name="Notify submitter",
        task_type=TaskType.CREATE_NOTIFICATION.value,
        is_start=False,
        max_attempts=1,
    )
    db.add_all((validate, approve, notify))
    db.flush()
    db.add_all(
        (
            RevisionTransition(
                revision_id=revision.id,
                from_task_id=validate.id,
                to_task_id=approve.id,
                condition="SUCCESS",
            ),
            RevisionTransition(
                revision_id=revision.id,
                from_task_id=validate.id,
                to_task_id=notify.id,
                condition="FAILURE",
            ),
        )
    )
    db.commit()
    return validate, approve, notify


def submit_invoice(
    db: Session,
    storage: LocalDocumentStorage,
    *,
    metadata: RawInvoiceMetadata | None = None,
    document: bytes | None = None,
) -> str:
    service = InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        storage,
        id_factory=iter(("invoice-1", "run-1")).__next__,
        clock=lambda: datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
    )
    result = service.submit(
        InvoiceSubmission(
            metadata=metadata
            or RawInvoiceMetadata(
                " Supplier ", " INV-001 ", "2026-08-13", "100.00", "EUR"
            ),
            original_filename="supplier-invoice.pdf",
            declared_media_type="application/pdf",
            document=BytesIO(document if document is not None else one_page_pdf()),
            mode=ExecutionMode.ORCHESTRATION,
        )
    )
    return result.run_id


def validation_service(
    uow: SqlAlchemyAutomaticStepUnitOfWork,
    storage: LocalDocumentStorage,
    *,
    commit_uow=None,
) -> AutomaticStepService:
    validation = DocumentValidationExecutor(uow, PypdfInspector(storage))
    success = SuccessfulExecutor()
    registry = AutomaticExecutorRegistry(
        {
            TaskType.DOCUMENT_VALIDATION: validation,
            TaskType.ARCHIVE_DOCUMENT: success,
            TaskType.CREATE_NOTIFICATION: success,
        }
    )
    return AutomaticStepService(
        commit_uow or uow,
        registry,
        TickingClock(),
        effect_policy=DocumentValidationEffectPolicy(uow),
    )


def trace_kinds(db: Session, run_id: str) -> list[str]:
    return list(
        db.scalars(
            select(InvoiceTraceEntry.observation_kind)
            .where(InvoiceTraceEntry.run_id == run_id)
            .order_by(InvoiceTraceEntry.position)
        )
    )


def test_valid_invoice_normalizes_metadata_and_advances_to_review(
    db: Session,
    tmp_path,
) -> None:
    _validate, approve, _notify = create_validation_revision(db)
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit_invoice(db, storage)
    uow = SqlAlchemyAutomaticStepUnitOfWork(db)

    completed = validation_service(uow, storage).execute(
        run_id, expected_state_version=1
    )

    invoice = db.get(Invoice, "invoice-1")
    cursor = db.get(ExecutionCursor, run_id)
    attempt = db.scalars(
        select(InvoiceTaskAttempt).where(InvoiceTaskAttempt.run_id == run_id)
    ).one()
    assert completed.committed_state_version == 2
    assert invoice.state == "SUBMITTED"
    assert invoice.supplier_name == "Supplier"
    assert invoice.invoice_number == "INV-001"
    assert invoice.amount == Decimal("100.00")
    assert invoice.currency == "EUR"
    assert cursor.current_task_id == approve.id
    assert cursor.state_version == 2
    assert attempt.outcome == "SUCCESS"
    assert trace_kinds(db, run_id) == [
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "TRANSITION_SELECTED",
    ]


@pytest.mark.parametrize(
    ("metadata", "document"),
    [
        (RawInvoiceMetadata(" ", "INV-1", "bad", "0", "eur"), None),
        (
            RawInvoiceMetadata(
                "Supplier", "INV-1", "2026-08-13", "10.00", "EUR"
            ),
            b"not a PDF",
        ),
    ],
)
def test_invalid_invoice_fails_visibly_without_approval_work(
    db: Session,
    tmp_path,
    metadata: RawInvoiceMetadata,
    document: bytes | None,
) -> None:
    _validate, _approve, notify = create_validation_revision(db)
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit_invoice(db, storage, metadata=metadata, document=document)
    uow = SqlAlchemyAutomaticStepUnitOfWork(db)

    validation_service(uow, storage).execute(run_id, expected_state_version=1)

    invoice = db.get(Invoice, "invoice-1")
    cursor = db.get(ExecutionCursor, run_id)
    attempt = db.scalars(
        select(InvoiceTaskAttempt).where(InvoiceTaskAttempt.run_id == run_id)
    ).one()
    assert invoice.state == "VALIDATION_FAILED"
    assert invoice.supplier_name is None
    assert cursor.current_task_id == notify.id
    assert cursor.state_version == 2
    assert attempt.outcome == "FAILURE"
    assert "document:" in attempt.reason or "issue_date:" in attempt.reason
    assert db.scalar(select(func.count()).select_from(ApprovalWorkItem)) == 0
    assert trace_kinds(db, run_id) == [
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "INVOICE_STATE_CHANGED",
        "TRANSITION_SELECTED",
    ]


def test_stale_database_version_rolls_back_the_whole_step(
    db: Session,
    tmp_path,
) -> None:
    create_validation_revision(db)
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit_invoice(db, storage)
    real_uow = SqlAlchemyAutomaticStepUnitOfWork(db)
    capturing = CapturingUnitOfWork(real_uow)
    validation_service(real_uow, storage, commit_uow=capturing).execute(
        run_id, expected_state_version=1
    )
    assert capturing.command is not None

    db.execute(
        update(ExecutionCursor)
        .where(ExecutionCursor.run_id == run_id)
        .values(state_version=2)
    )
    db.commit()

    with pytest.raises(StateVersionConflict):
        real_uow.commit_automatic_step(capturing.command)

    invoice = db.get(Invoice, "invoice-1")
    assert invoice.supplier_name is None
    assert db.scalar(select(func.count()).select_from(InvoiceTaskAttempt)) == 0
    assert trace_kinds(db, run_id) == ["RUN_STARTED"]
