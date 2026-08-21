from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.application.approval import (
    ApprovalDecisionConflict,
    CommitApprovalDecisionCommand,
    HumanApprovalService,
    WaitingHumanApproval,
)
from app.application.errors import StateVersionConflict
from app.domain.approval import (
    ApprovalChoice,
    ApprovalDecisionError,
    ApprovalDecisionInput,
)
from app.domain.types import TaskOutcome, TransitionSelected
from app.persistence.approval import (
    SqlAlchemyApprovalQueryService,
    SqlAlchemyApprovalUnitOfWork,
)
from app.persistence.models import (
    ApprovalDecision as ApprovalDecisionRow,
    ApprovalWorkItem,
    ExecutionCursor,
    Invoice,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
    RevisionTransition,
    WorkflowDraft,
    WorkflowRevision,
)


class TickingClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 13, 13, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(milliseconds=1)
        return value


class CapturingApprovalUnitOfWork:
    def __init__(self, delegate: SqlAlchemyApprovalUnitOfWork) -> None:
        self.delegate = delegate
        self.command: CommitApprovalDecisionCommand | None = None

    def load_human_approval(self, run_id: str):
        return self.delegate.load_human_approval(run_id)

    def commit_wait(self, command) -> None:
        self.delegate.commit_wait(command)

    def load_approval_decision(self, work_item_id: str):
        return self.delegate.load_approval_decision(work_item_id)

    def commit_decision(self, command: CommitApprovalDecisionCommand) -> None:
        self.command = command


def create_ready_approval(
    db: Session,
    suffix: str = "1",
) -> tuple[str, str, RevisionTask, RevisionTask, RevisionTask]:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    draft = WorkflowDraft(
        name=f"Invoice {suffix}",
        created_at=now,
        updated_at=now,
    )
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
    review = RevisionTask(
        revision_id=revision.id,
        task_key="review",
        name="Review invoice",
        task_type="HUMAN_APPROVAL",
        is_start=False,
        max_attempts=None,
    )
    archive = RevisionTask(
        revision_id=revision.id,
        task_key="archive",
        name="Archive invoice",
        task_type="ARCHIVE_DOCUMENT",
        is_start=False,
        max_attempts=2,
    )
    notify = RevisionTask(
        revision_id=revision.id,
        task_key="notify",
        name="Notify submitter",
        task_type="CREATE_NOTIFICATION",
        is_start=False,
        max_attempts=2,
    )
    db.add_all((review, archive, notify))
    db.flush()
    db.add_all(
        (
            RevisionTransition(
                revision_id=revision.id,
                from_task_id=review.id,
                to_task_id=archive.id,
                condition="SUCCESS",
            ),
            RevisionTransition(
                revision_id=revision.id,
                from_task_id=review.id,
                to_task_id=notify.id,
                condition="FAILURE",
            ),
        )
    )
    invoice_id = f"invoice-{suffix}"
    run_id = f"run-{suffix}"
    invoice = Invoice(
        id=invoice_id,
        supplier_name_raw="Supplier",
        invoice_number_raw=f"INV-{suffix}",
        issue_date_raw="2026-08-13",
        amount_raw="100.00",
        currency_raw="EUR",
        supplier_name="Supplier",
        invoice_number=f"INV-{suffix}",
        issue_date=None,
        amount=None,
        currency="EUR",
        document_identity=(suffix * 32)[:32],
        original_filename="invoice.pdf",
        declared_media_type="application/pdf",
        document_size_bytes=100,
        state="SUBMITTED",
        created_at=now,
    )
    db.add(invoice)
    db.flush()
    run = InvoiceWorkflowRun(
        id=run_id,
        invoice_id=invoice_id,
        revision_id=revision.id,
        mode="orchestration",
        scenario="standard",
        status="RUNNING",
        started_at=now,
        finished_at=None,
    )
    db.add(run)
    db.flush()
    db.add_all(
        (
            ExecutionCursor(
                run_id=run_id,
                current_task_id=review.id,
                phase="READY",
                state_version=2,
                terminal_decision=None,
            ),
            InvoiceTraceEntry(
                run_id=run_id,
                position=1,
                observation_kind="RUN_STARTED",
                task_id=review.id,
                attempt_ordinal=None,
                detail=None,
                timestamp=now,
            ),
        )
    )
    db.commit()
    return run_id, invoice_id, review, archive, notify


def service(db: Session, *ids: str) -> HumanApprovalService:
    generated = iter(ids)
    return HumanApprovalService(
        SqlAlchemyApprovalUnitOfWork(db),
        id_factory=lambda: next(generated),
        clock=TickingClock(),
    )


def trace_kinds(db: Session, run_id: str) -> list[str]:
    return list(
        db.scalars(
            select(InvoiceTraceEntry.observation_kind)
            .where(InvoiceTraceEntry.run_id == run_id)
            .order_by(InvoiceTraceEntry.position)
        )
    )


def test_enter_wait_is_persistent_and_duplicate_delivery_is_idempotent(
    db: Session,
) -> None:
    run_id, invoice_id, review, _archive, _notify = create_ready_approval(db)
    approval = service(db, "work-1")

    first = approval.enter_wait(run_id, expected_state_version=2)
    replay = approval.enter_wait(run_id, expected_state_version=2)

    cursor = db.get(ExecutionCursor, run_id)
    run = db.get(InvoiceWorkflowRun, run_id)
    invoice = db.get(Invoice, invoice_id)
    item = db.get(ApprovalWorkItem, "work-1")
    assert first.replayed is False
    assert replay.replayed is True
    assert replay.work_item_id == first.work_item_id
    assert cursor.phase == "WAITING_FOR_APPROVAL"
    assert cursor.current_task_id == review.id
    assert cursor.state_version == 3
    assert run.status == "WAITING_FOR_APPROVAL"
    assert invoice.state == "PENDING_APPROVAL"
    assert item.state == "PENDING"
    assert db.scalar(select(func.count()).select_from(ApprovalWorkItem)) == 1
    assert trace_kinds(db, run_id) == [
        "RUN_STARTED",
        "INVOICE_STATE_CHANGED",
        "WAITING_FOR_APPROVAL",
    ]

    with Session(db.get_bind()) as restarted_session:
        restored = SqlAlchemyApprovalUnitOfWork(
            restarted_session
        ).load_human_approval(run_id)
        assert isinstance(restored, WaitingHumanApproval)
        assert restored.work_item_id == "work-1"


def test_pending_query_exposes_invoice_and_run_context(db: Session) -> None:
    run_id, invoice_id, _review, _archive, _notify = create_ready_approval(db)
    approval = service(db, "work-1")
    approval.enter_wait(run_id, expected_state_version=2)

    queries = SqlAlchemyApprovalQueryService(db)
    listed = queries.list_pending()
    detail = queries.get("work-1")

    assert listed == (detail,)
    assert detail.run_id == run_id
    assert detail.invoice_id == invoice_id
    assert detail.supplier_name == "Supplier"
    assert detail.invoice_number == "INV-1"
    assert detail.document_identity == "1" * 32
    assert detail.approval_state == "PENDING"
    assert detail.invoice_state == "PENDING_APPROVAL"
    assert detail.run_status == "WAITING_FOR_APPROVAL"
    assert detail.state_version == 3


def test_approve_resumes_same_run_and_identical_replay_changes_nothing(
    db: Session,
) -> None:
    run_id, invoice_id, _review, archive, _notify = create_ready_approval(db)
    approval = service(db, "work-1", "decision-1")
    approval.enter_wait(run_id, expected_state_version=2)
    value = ApprovalDecisionInput(ApprovalChoice.APPROVE, note="Looks correct")

    accepted = approval.decide("work-1", value, expected_state_version=3)
    trace_count = db.scalar(select(func.count()).select_from(InvoiceTraceEntry))
    replay = approval.decide("work-1", value, expected_state_version=3)

    cursor = db.get(ExecutionCursor, run_id)
    run = db.get(InvoiceWorkflowRun, run_id)
    invoice = db.get(Invoice, invoice_id)
    item = db.get(ApprovalWorkItem, "work-1")
    decision = db.get(ApprovalDecisionRow, "decision-1")
    assert accepted.replayed is False
    assert accepted.outcome is TaskOutcome.SUCCESS
    assert isinstance(accepted.resolution, TransitionSelected)
    assert replay.replayed is True
    assert cursor.phase == "READY"
    assert cursor.current_task_id == archive.id
    assert cursor.state_version == 4
    assert run.id == run_id
    assert run.status == "RUNNING"
    assert invoice.state == "APPROVED"
    assert item.state == "APPROVED"
    assert decision.decision == "APPROVE"
    assert decision.note == "Looks correct"
    assert db.scalar(select(func.count()).select_from(ApprovalDecisionRow)) == 1
    assert db.scalar(select(func.count()).select_from(InvoiceTraceEntry)) == trace_count
    assert trace_kinds(db, run_id)[-4:] == [
        "APPROVAL_DECIDED",
        "INVOICE_STATE_CHANGED",
        "RUN_RESUMED",
        "TRANSITION_SELECTED",
    ]

    with pytest.raises(ApprovalDecisionConflict):
        approval.decide(
            "work-1",
            ApprovalDecisionInput(ApprovalChoice.REJECT, reason="Duplicate"),
        )
    assert db.scalar(select(func.count()).select_from(ApprovalDecisionRow)) == 1


def test_reject_trims_reason_and_uses_failure_route(db: Session) -> None:
    run_id, invoice_id, _review, _archive, notify = create_ready_approval(db)
    approval = service(db, "work-1", "decision-1")
    approval.enter_wait(run_id, expected_state_version=2)

    accepted = approval.decide(
        "work-1",
        ApprovalDecisionInput(
            ApprovalChoice.REJECT,
            reason="  Amount requires correction  ",
        ),
        expected_state_version=3,
    )

    cursor = db.get(ExecutionCursor, run_id)
    invoice = db.get(Invoice, invoice_id)
    decision = db.get(ApprovalDecisionRow, "decision-1")
    assert accepted.outcome is TaskOutcome.FAILURE
    assert cursor.current_task_id == notify.id
    assert invoice.state == "REJECTED"
    assert decision.reason == "Amount requires correction"
    assert decision.note is None


def test_invalid_or_stale_decision_cannot_change_waiting_state(db: Session) -> None:
    run_id, invoice_id, _review, _archive, _notify = create_ready_approval(db)
    approval = service(db, "work-1", "decision-1")
    approval.enter_wait(run_id, expected_state_version=2)

    with pytest.raises(ApprovalDecisionError):
        approval.decide(
            "work-1",
            ApprovalDecisionInput(ApprovalChoice.REJECT, reason="   "),
        )
    with pytest.raises(StateVersionConflict):
        approval.decide(
            "work-1",
            ApprovalDecisionInput(ApprovalChoice.APPROVE),
            expected_state_version=99,
        )

    assert db.get(ExecutionCursor, run_id).state_version == 3
    assert db.get(Invoice, invoice_id).state == "PENDING_APPROVAL"
    assert db.scalar(select(func.count()).select_from(ApprovalDecisionRow)) == 0


def test_deciding_one_waiting_run_does_not_change_another(db: Session) -> None:
    run_1, invoice_1, _review_1, _archive_1, _notify_1 = create_ready_approval(
        db, "1"
    )
    run_2, invoice_2, _review_2, _archive_2, _notify_2 = create_ready_approval(
        db, "2"
    )
    approval_1 = service(db, "work-1", "decision-1")
    approval_2 = service(db, "work-2")
    approval_1.enter_wait(run_1, expected_state_version=2)
    approval_2.enter_wait(run_2, expected_state_version=2)

    approval_1.decide(
        "work-1",
        ApprovalDecisionInput(ApprovalChoice.APPROVE),
        expected_state_version=3,
    )

    assert db.get(Invoice, invoice_1).state == "APPROVED"
    assert db.get(ExecutionCursor, run_1).phase == "READY"
    assert db.get(Invoice, invoice_2).state == "PENDING_APPROVAL"
    assert db.get(ExecutionCursor, run_2).phase == "WAITING_FOR_APPROVAL"
    assert db.get(ApprovalWorkItem, "work-2").state == "PENDING"


def test_database_version_race_rolls_back_decision_and_trace(db: Session) -> None:
    run_id, invoice_id, _review, _archive, _notify = create_ready_approval(db)
    real_uow = SqlAlchemyApprovalUnitOfWork(db)
    HumanApprovalService(
        real_uow,
        id_factory=lambda: "work-1",
        clock=TickingClock(),
    ).enter_wait(run_id, expected_state_version=2)
    capturing = CapturingApprovalUnitOfWork(real_uow)
    approval = HumanApprovalService(
        capturing,
        id_factory=lambda: "decision-1",
        clock=TickingClock(),
    )

    approval.decide(
        "work-1",
        ApprovalDecisionInput(ApprovalChoice.APPROVE),
        expected_state_version=3,
    )
    assert capturing.command is not None
    db.execute(
        update(ExecutionCursor)
        .where(ExecutionCursor.run_id == run_id)
        .values(state_version=4)
    )
    db.commit()

    with pytest.raises(StateVersionConflict):
        real_uow.commit_decision(capturing.command)

    assert db.get(Invoice, invoice_id).state == "PENDING_APPROVAL"
    assert db.get(ApprovalWorkItem, "work-1").state == "PENDING"
    assert db.scalar(select(func.count()).select_from(ApprovalDecisionRow)) == 0
    assert trace_kinds(db, run_id)[-1] == "WAITING_FOR_APPROVAL"
