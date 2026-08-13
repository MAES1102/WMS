from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.application.invoice_validation import MAX_PDF_BYTES
from app.application.submission import InvoiceSubmissionService
from app.db import Base
from app.infrastructure.documents import LocalDocumentStorage
from app.persistence.models import (
    Invoice,
    InvoiceWorkflowRun,
    RevisionTask,
    WorkflowDraft,
    WorkflowRevision,
)
from app.persistence.submission import SqlAlchemySubmissionUnitOfWork
from app.presentation.submission_api import create_submission_router


V3_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name.startswith("invoice_") or table.name == "invoices"
)


@pytest.fixture()
def api(db: Session, tmp_path) -> TestClient:
    storage = LocalDocumentStorage(tmp_path)
    ids = iter(("invoice-http-1", "run-http-1"))

    def service() -> InvoiceSubmissionService:
        return InvoiceSubmissionService(
            SqlAlchemySubmissionUnitOfWork(db),
            storage,
            id_factory=lambda: next(ids),
            clock=lambda: datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
        )

    app = FastAPI()
    app.include_router(create_submission_router(service))
    return TestClient(app)


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine, tables=V3_TABLES)
    with Session(engine) as session:
        yield session
        session.rollback()
    Base.metadata.drop_all(engine, tables=V3_TABLES)


def activate_revision(db: Session) -> None:
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
    db.add(
        RevisionTask(
            revision_id=revision.id,
            task_key="validate",
            name="Validate invoice",
            task_type="DOCUMENT_VALIDATION",
            is_start=True,
            max_attempts=1,
        )
    )
    db.commit()


def fields(**changes) -> dict[str, str]:
    values = {
        "supplier_name": "Supplier",
        "invoice_number": "INV-HTTP-1",
        "issue_date": "2026-08-13",
        "amount": "125.50",
        "currency": "EUR",
        "mode": "orchestration",
    }
    values.update(changes)
    return values


def test_multipart_submission_returns_business_identities(
    api: TestClient,
    db: Session,
) -> None:
    activate_revision(db)

    response = api.post(
        "/api/v3/invoices",
        data=fields(),
        files={"document": ("invoice.pdf", b"%PDF-bounded", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "invoice_id": "invoice-http-1",
        "run_id": "run-http-1",
        "invoice_state": "SUBMITTED",
        "run_status": "RUNNING",
        "state_version": 1,
    }
    invoice = db.get(Invoice, "invoice-http-1")
    run = db.get(InvoiceWorkflowRun, "run-http-1")
    assert invoice.invoice_number_raw == "INV-HTTP-1"
    assert invoice.original_filename == "invoice.pdf"
    assert run.invoice_id == invoice.id


def test_business_invalid_metadata_is_accepted_for_workflow_validation(
    api: TestClient,
    db: Session,
) -> None:
    activate_revision(db)

    response = api.post(
        "/api/v3/invoices",
        data=fields(issue_date="bad", amount="0", currency="eur"),
        files={"document": ("invoice.pdf", b"not yet inspected", "application/pdf")},
    )

    assert response.status_code == 201
    invoice = db.get(Invoice, "invoice-http-1")
    assert invoice.state == "SUBMITTED"
    assert invoice.issue_date_raw == "bad"
    assert invoice.issue_date is None


def test_boundary_rejects_non_multipart_missing_duplicate_and_oversize(
    api: TestClient,
    db: Session,
) -> None:
    activate_revision(db)

    non_multipart = api.post(
        "/api/v3/invoices",
        content=b"not multipart",
        headers={"content-type": "application/pdf"},
    )
    missing = api.post(
        "/api/v3/invoices",
        data={key: value for key, value in fields().items() if key != "currency"},
        files={"document": ("invoice.pdf", b"pdf", "application/pdf")},
    )
    duplicate = api.post(
        "/api/v3/invoices",
        data=fields(),
        files=[
            ("document", ("one.pdf", b"one", "application/pdf")),
            ("document", ("two.pdf", b"two", "application/pdf")),
        ],
    )
    oversize = api.post(
        "/api/v3/invoices",
        data=fields(),
        files={
            "document": (
                "large.pdf",
                b"x" * (MAX_PDF_BYTES + 1),
                "application/pdf",
            )
        },
    )

    assert non_multipart.status_code == 415
    assert missing.status_code == 422
    assert duplicate.status_code == 422
    assert oversize.status_code == 413
    assert db.scalar(select(func.count()).select_from(Invoice)) == 0


def test_missing_active_revision_is_a_visible_conflict(
    api: TestClient,
    db: Session,
) -> None:
    response = api.post(
        "/api/v3/invoices",
        data=fields(),
        files={"document": ("invoice.pdf", b"pdf", "application/pdf")},
    )

    assert response.status_code == 409
    assert "active workflow" in response.json()["detail"].lower()
    assert db.scalar(select(func.count()).select_from(Invoice)) == 0
