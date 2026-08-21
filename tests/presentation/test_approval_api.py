from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.application.approval import HumanApprovalService
from app.persistence.database import Base
from app.persistence.approval import (
    SqlAlchemyApprovalQueryService,
    SqlAlchemyApprovalUnitOfWork,
)
from app.persistence.models import ApprovalDecision as ApprovalDecisionRow
from app.presentation.approval_api import create_approval_router
from tests.persistence.test_approval import create_ready_approval


INVOICE_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name.startswith("invoice_") or table.name == "invoices"
)


class TickingClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 13, 14, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(milliseconds=1)
        return value


@pytest.fixture()
def approval_api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine, tables=INVOICE_TABLES)
    with Session(engine) as db:
        run_id, _invoice_id, _review, _archive, _notify = create_ready_approval(db)
        ids = iter(("work-http-1", "decision-http-1"))
        service = HumanApprovalService(
            SqlAlchemyApprovalUnitOfWork(db),
            id_factory=lambda: next(ids),
            clock=TickingClock(),
        )
        service.enter_wait(run_id, expected_state_version=2)
        queries = SqlAlchemyApprovalQueryService(db)
        app = FastAPI()
        app.include_router(
            create_approval_router(
                service_dependency=lambda: service,
                query_dependency=lambda: queries,
            )
        )
        with TestClient(app) as client:
            yield client, db
        db.rollback()
    Base.metadata.drop_all(engine, tables=INVOICE_TABLES)


def test_pending_list_and_detail_lead_with_invoice_context(approval_api) -> None:
    client, _db = approval_api

    listed = client.get("/api/v3/approvals")
    detail = client.get("/api/v3/approvals/work-http-1")

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json() == [detail.json()]
    assert detail.json()["supplier_name"] == "Supplier"
    assert detail.json()["invoice_number"] == "INV-1"
    assert detail.json()["invoice_state"] == "PENDING_APPROVAL"
    assert detail.json()["run_status"] == "WAITING_FOR_APPROVAL"
    assert detail.json()["state_version"] == 3


def test_approve_then_identical_replay_is_visible_and_idempotent(
    approval_api,
) -> None:
    client, db = approval_api
    payload = {
        "choice": "APPROVE",
        "note": "Looks correct",
        "expected_state_version": 3,
    }

    accepted = client.post(
        "/api/v3/approvals/work-http-1/decision",
        json=payload,
    )
    replay = client.post(
        "/api/v3/approvals/work-http-1/decision",
        json=payload,
    )

    assert accepted.status_code == 200
    assert accepted.json()["outcome"] == "SUCCESS"
    assert accepted.json()["state_version"] == 4
    assert accepted.json()["replayed"] is False
    assert accepted.json()["resume_required"] is True
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["resume_required"] is False
    assert db.get(ApprovalDecisionRow, "decision-http-1").note == "Looks correct"
    assert client.get("/api/v3/approvals").json() == []


def test_conflicting_or_invalid_decision_is_controlled(approval_api) -> None:
    client, _db = approval_api
    accepted = client.post(
        "/api/v3/approvals/work-http-1/decision",
        json={"choice": "APPROVE", "expected_state_version": 3},
    )
    conflict = client.post(
        "/api/v3/approvals/work-http-1/decision",
        json={"choice": "REJECT", "reason": "Duplicate"},
    )
    missing_reason = client.post(
        "/api/v3/approvals/missing/decision",
        json={"choice": "REJECT", "reason": "   "},
    )
    missing_item = client.get("/api/v3/approvals/missing")

    assert accepted.status_code == 200
    assert conflict.status_code == 409
    assert missing_reason.status_code == 422
    assert missing_item.status_code == 404
