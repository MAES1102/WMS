from datetime import UTC, datetime
from io import BytesIO

import pytest
from pypdf import PdfWriter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.submission import (
    InvoiceSubmission,
    InvoiceSubmissionService,
    SubmissionConflict,
)
from app.domain.invoice import RawInvoiceMetadata
from app.domain.types import ExecutionMode
from app.infrastructure.documents import LocalDocumentStorage
from app.persistence.models import (
    ExecutionCursor,
    Invoice,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
    WorkflowDraft,
    WorkflowRevision,
)
from app.persistence.submission import (
    ActiveWorkflowNotFound,
    SqlAlchemySubmissionUnitOfWork,
)


def create_active_revision(db: Session) -> tuple[WorkflowRevision, RevisionTask]:
    now = datetime(2026, 8, 13, tzinfo=UTC)
    draft = WorkflowDraft(name="Invoice", created_at=now, updated_at=now)
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
    start = RevisionTask(
        revision_id=revision.id,
        task_key="validate",
        name="Validate invoice",
        task_type="DOCUMENT_VALIDATION",
        is_start=True,
        max_attempts=1,
    )
    db.add(start)
    db.commit()
    return revision, start


def one_page_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def submission(**changes) -> InvoiceSubmission:
    values = {
        "metadata": RawInvoiceMetadata(
            " Supplier ",
            " INV-001 ",
            "2026-08-13",
            "100.00",
            "EUR",
        ),
        "original_filename": "../../supplier-invoice.pdf",
        "declared_media_type": "application/pdf",
        "document": BytesIO(one_page_pdf()),
        "mode": ExecutionMode.ORCHESTRATION,
    }
    values.update(changes)
    return InvoiceSubmission(**values)


def test_submission_atomically_creates_invoice_run_cursor_and_trace(
    db: Session,
    tmp_path,
) -> None:
    revision, start = create_active_revision(db)
    ids = iter(("invoice-1", "run-1"))
    storage = LocalDocumentStorage(tmp_path)
    service = InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        storage,
        id_factory=lambda: next(ids),
        clock=lambda: datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
    )

    result = service.submit(submission())

    invoice = db.get(Invoice, result.invoice_id)
    run = db.get(InvoiceWorkflowRun, result.run_id)
    cursor = db.get(ExecutionCursor, result.run_id)
    trace = db.scalars(
        select(InvoiceTraceEntry).where(
            InvoiceTraceEntry.run_id == result.run_id
        )
    ).one()
    assert invoice.state == "SUBMITTED"
    assert invoice.supplier_name_raw == " Supplier "
    assert invoice.supplier_name is None
    assert invoice.original_filename == "../../supplier-invoice.pdf"
    assert run.invoice_id == invoice.id
    assert run.revision_id == revision.id
    assert run.mode == "orchestration"
    assert cursor.current_task_id == start.id
    assert cursor.phase == "READY"
    assert cursor.state_version == 1
    assert trace.observation_kind == "RUN_STARTED"
    assert trace.position == 1
    assert [path.name for path in tmp_path.iterdir()] == [
        f"{invoice.document_identity}.pdf"
    ]


def test_business_invalid_raw_metadata_is_still_submitted_for_validation(
    db: Session,
    tmp_path,
) -> None:
    create_active_revision(db)
    ids = iter(("invoice-invalid", "run-invalid"))
    service = InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        LocalDocumentStorage(tmp_path),
        id_factory=lambda: next(ids),
    )
    invalid = RawInvoiceMetadata(" ", "x" * 65, "bad", "0", "eur")

    result = service.submit(submission(metadata=invalid))

    invoice = db.get(Invoice, result.invoice_id)
    assert invoice.state == "SUBMITTED"
    assert invoice.invoice_number_raw == "x" * 65
    assert invoice.invoice_number is None
    assert invoice.issue_date_raw == "bad"
    assert invoice.issue_date is None


def test_database_failure_rolls_back_records_and_removes_new_document(
    db: Session,
    tmp_path,
) -> None:
    create_active_revision(db)
    ids = iter(("invoice-1", "run-1", "invoice-1", "run-2"))
    storage = LocalDocumentStorage(tmp_path)
    service = InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        storage,
        id_factory=lambda: next(ids),
    )
    service.submit(submission())

    with pytest.raises(SubmissionConflict):
        service.submit(submission())

    assert db.scalar(select(func.count()).select_from(Invoice)) == 1
    assert db.scalar(select(func.count()).select_from(InvoiceWorkflowRun)) == 1
    assert db.scalar(select(func.count()).select_from(ExecutionCursor)) == 1
    assert db.scalar(select(func.count()).select_from(InvoiceTraceEntry)) == 1
    assert len(list(tmp_path.iterdir())) == 1


def test_missing_active_revision_fails_before_document_storage(
    db: Session,
    tmp_path,
) -> None:
    service = InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        LocalDocumentStorage(tmp_path),
    )

    with pytest.raises(ActiveWorkflowNotFound):
        service.submit(submission())

    assert list(tmp_path.iterdir()) == []
