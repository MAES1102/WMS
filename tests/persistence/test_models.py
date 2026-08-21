from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    ApprovalDecision,
    ApprovalWorkItem,
    DraftTask,
    ExecutionCursor,
    Invoice,
    InvoiceTaskAttempt,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
    WorkflowDraft,
    WorkflowRevision,
)


EXPECTED_TABLES = {
    "invoice_approval_decisions",
    "invoice_approval_work_items",
    "invoice_archive_records",
    "invoice_draft_tasks",
    "invoice_draft_transitions",
    "invoice_execution_cursors",
    "invoice_internal_notifications",
    "invoice_revision_tasks",
    "invoice_revision_transitions",
    "invoice_task_attempts",
    "invoice_trace_entries",
    "invoice_workflow_drafts",
    "invoice_workflow_revisions",
    "invoice_workflow_runs",
    "invoices",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _foundation(db: Session) -> tuple[RevisionTask, InvoiceWorkflowRun]:
    draft = WorkflowDraft(name="Invoice approval", created_at=_now(), updated_at=_now())
    db.add(draft)
    db.flush()
    revision = WorkflowRevision(
        draft_id=draft.id,
        revision_number=1,
        name=draft.name,
        activated_at=_now(),
    )
    db.add(revision)
    db.flush()
    task = RevisionTask(
        revision_id=revision.id,
        task_key="validate",
        name="Validate",
        task_type="DOCUMENT_VALIDATION",
        is_start=True,
        max_attempts=1,
    )
    invoice = Invoice(
        id="invoice-1",
        supplier_name_raw="Supplier",
        invoice_number_raw="INV-001",
        issue_date_raw="2026-08-13",
        amount_raw="100.00",
        currency_raw="EUR",
        supplier_name="Supplier",
        invoice_number="INV-001",
        issue_date=date(2026, 8, 13),
        amount=Decimal("100.00"),
        currency="EUR",
        document_identity="document-1",
        original_filename="invoice.pdf",
        declared_media_type="application/pdf",
        document_size_bytes=128,
        state="SUBMITTED",
        created_at=_now(),
    )
    db.add_all((task, invoice))
    db.flush()
    run = InvoiceWorkflowRun(
        id="run-1",
        invoice_id=invoice.id,
        revision_id=revision.id,
        mode="orchestration",
        scenario="standard",
        status="RUNNING",
        started_at=_now(),
    )
    db.add(run)
    db.flush()
    return task, run


def _assert_integrity_error(db: Session, record: object) -> None:
    db.add(record)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_fresh_schema_contains_only_the_invoice_manifest(
    invoice_table_names: set[str],
) -> None:
    assert invoice_table_names == EXPECTED_TABLES


def test_invoice_can_retain_invalid_raw_values_before_validation(db: Session) -> None:
    invoice = Invoice(
        id="invoice-invalid",
        supplier_name_raw=" " * 121,
        invoice_number_raw="INV-INVALID",
        issue_date_raw="not-a-date",
        amount_raw="not-a-decimal",
        currency_raw="euro",
        supplier_name=None,
        invoice_number=None,
        issue_date=None,
        amount=None,
        currency=None,
        document_identity="document-invalid",
        original_filename="../../untrusted-name.pdf",
        declared_media_type="text/plain",
        document_size_bytes=0,
        state="SUBMITTED",
        created_at=_now(),
    )
    db.add(invoice)
    db.flush()

    assert invoice.issue_date_raw == "not-a-date"
    assert len(invoice.supplier_name_raw) == 121
    assert invoice.supplier_name is None
    assert invoice.amount is None
    assert invoice.original_filename == "../../untrusted-name.pdf"


def test_draft_task_bound_depends_on_task_type(db: Session) -> None:
    draft = WorkflowDraft(name="Draft", created_at=_now(), updated_at=_now())
    db.add(draft)
    db.flush()
    db.add(
        DraftTask(
            draft_id=draft.id,
            task_key="approve",
            name="Approve",
            task_type="HUMAN_APPROVAL",
            is_start=True,
            max_attempts=None,
        )
    )
    db.flush()
    _assert_integrity_error(
        db,
        DraftTask(
            draft_id=draft.id,
            task_key="archive",
            name="Archive",
            task_type="ARCHIVE_DOCUMENT",
            is_start=False,
            max_attempts=0,
        ),
    )


def test_revision_content_rejects_orm_update(db: Session) -> None:
    task, _run = _foundation(db)
    db.commit()

    task.name = "Renamed after activation"
    with pytest.raises(ValueError, match="immutable"):
        db.flush()


def test_cursor_requires_version_and_terminal_consistency(db: Session) -> None:
    task, run = _foundation(db)
    _assert_integrity_error(
        db,
        ExecutionCursor(
            run_id=run.id,
            current_task_id=task.id,
            phase="READY",
            state_version=0,
            terminal_decision=None,
        ),
    )

    task, run = _foundation(db)
    _assert_integrity_error(
        db,
        ExecutionCursor(
            run_id=run.id,
            current_task_id=task.id,
            phase="TERMINAL",
            state_version=1,
            terminal_decision=None,
        ),
    )


def test_attempt_result_and_ordinal_are_run_unique(db: Session) -> None:
    task, run = _foundation(db)
    first = InvoiceTaskAttempt(
        run_id=run.id,
        task_id=task.id,
        attempt_ordinal=1,
        outcome="FAILURE",
        failure_class="RETRYABLE_TECHNICAL",
        reason="temporary",
        started_at=_now(),
        finished_at=_now(),
    )
    db.add(first)
    db.flush()
    _assert_integrity_error(
        db,
        InvoiceTaskAttempt(
            run_id=run.id,
            task_id=task.id,
            attempt_ordinal=1,
            outcome="SUCCESS",
            failure_class=None,
            started_at=_now(),
            finished_at=_now(),
        ),
    )


def test_work_item_and_decision_are_single_authoritative_records(db: Session) -> None:
    task, run = _foundation(db)
    item = ApprovalWorkItem(
        id="item-1",
        run_id=run.id,
        invoice_id=run.invoice_id,
        task_id=task.id,
        state="PENDING",
        created_at=_now(),
    )
    db.add(item)
    db.flush()
    db.add(
        ApprovalDecision(
            id="decision-1",
            work_item_id=item.id,
            decision="REJECT",
            reason="Missing purchase order",
            decided_at=_now(),
        )
    )
    db.flush()
    _assert_integrity_error(
        db,
        ApprovalDecision(
            id="decision-2",
            work_item_id=item.id,
            decision="APPROVE",
            note="conflict",
            decided_at=_now(),
        ),
    )


def test_rejection_requires_non_blank_reason(db: Session) -> None:
    task, run = _foundation(db)
    item = ApprovalWorkItem(
        id="item-1",
        run_id=run.id,
        invoice_id=run.invoice_id,
        task_id=task.id,
        state="PENDING",
        created_at=_now(),
    )
    db.add(item)
    db.flush()
    _assert_integrity_error(
        db,
        ApprovalDecision(
            id="decision-1",
            work_item_id=item.id,
            decision="REJECT",
            reason="   ",
            decided_at=_now(),
        ),
    )


def test_trace_position_and_attempt_ordinal_are_bounded(db: Session) -> None:
    _task, run = _foundation(db)
    db.add(
        InvoiceTraceEntry(
            run_id=run.id,
            position=1,
            observation_kind="RUN_STARTED",
            timestamp=_now(),
        )
    )
    db.flush()
    _assert_integrity_error(
        db,
        InvoiceTraceEntry(
            run_id=run.id,
            position=1,
            observation_kind="ATTEMPT_OUTCOME",
            attempt_ordinal=0,
            timestamp=_now(),
        ),
    )
