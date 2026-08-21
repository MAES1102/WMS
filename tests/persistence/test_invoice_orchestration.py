from datetime import UTC, datetime, timedelta
from io import BytesIO

from pypdf import PdfWriter
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.persistence.database import Base
from app.application.approval import HumanApprovalService
from app.application.choreography import InvoiceChoreographer
from app.application.executors import (
    AutomaticExecutorRegistry,
    DeterministicFaultExecutor,
    DeterministicFaultSchedule,
    FaultKey,
)
from app.application.invoice_tasks import (
    ArchiveDocumentExecutor,
    CompositeAutomaticStepEffectPolicy,
    CreateNotificationExecutor,
    InvoiceBusinessEffectPolicy,
)
from app.application.invoice_validation import (
    DocumentValidationEffectPolicy,
    DocumentValidationExecutor,
)
from app.application.orchestration import (
    CursorPhase,
    InvoiceExecutionCoordinator,
    InvoiceOrchestrator,
)
from app.application.step_service import AutomaticStepService
from app.application.submission import (
    InvoiceSubmission,
    InvoiceSubmissionService,
)
from app.domain.approval import (
    ApprovalChoice,
    ApprovalDecisionInput,
)
from app.domain.invoice import RawInvoiceMetadata
from app.domain.types import (
    ExecutionMode,
    FailureClass,
    TaskOutcome,
    TaskResult,
    TaskType,
    TerminalDecision,
)
from app.infrastructure.documents import LocalDocumentStorage
from app.infrastructure.event_bus import InMemoryRunEventBus
from app.infrastructure.pdf import PypdfInspector
from app.persistence.approval import SqlAlchemyApprovalUnitOfWork
from app.persistence.models import (
    ApprovalWorkItem,
    ArchiveRecord,
    InternalNotification,
    Invoice,
    InvoiceTaskAttempt,
    RevisionTask,
    RevisionTransition,
    WorkflowDraft,
    WorkflowRevision,
)
from app.persistence.orchestration import (
    SqlAlchemyInvoiceRunQueryService,
    SqlAlchemyRunControlReader,
)
from app.persistence.step import SqlAlchemyAutomaticStepUnitOfWork
from app.persistence.submission import SqlAlchemySubmissionUnitOfWork


RETRYABLE_ARCHIVE_FAILURE = TaskResult(
    TaskOutcome.FAILURE,
    FailureClass.RETRYABLE_TECHNICAL,
    "archive storage temporarily unavailable",
)


class TickingClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 13, 14, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(milliseconds=1)
        return value


def one_page_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def create_reference_revision(
    db: Session,
) -> tuple[RevisionTask, RevisionTask, RevisionTask, RevisionTask]:
    now = datetime(2026, 8, 13, 13, 0, tzinfo=UTC)
    draft = WorkflowDraft(
        name="Invoice approval",
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
    validate = RevisionTask(
        revision_id=revision.id,
        task_key="validate",
        name="Validate invoice",
        task_type=TaskType.DOCUMENT_VALIDATION.value,
        is_start=True,
        max_attempts=1,
    )
    review = RevisionTask(
        revision_id=revision.id,
        task_key="review",
        name="Review invoice",
        task_type=TaskType.HUMAN_APPROVAL.value,
        is_start=False,
        max_attempts=None,
    )
    archive = RevisionTask(
        revision_id=revision.id,
        task_key="archive",
        name="Archive invoice",
        task_type=TaskType.ARCHIVE_DOCUMENT.value,
        is_start=False,
        max_attempts=2,
    )
    notify = RevisionTask(
        revision_id=revision.id,
        task_key="notify",
        name="Notify submitter",
        task_type=TaskType.CREATE_NOTIFICATION.value,
        is_start=False,
        max_attempts=2,
    )
    db.add_all((validate, review, archive, notify))
    db.flush()
    transitions = (
        (validate, review, "SUCCESS"),
        (validate, notify, "FAILURE"),
        (review, archive, "SUCCESS"),
        (review, notify, "FAILURE"),
        (archive, notify, "SUCCESS"),
        (archive, notify, "FAILURE"),
    )
    db.add_all(
        RevisionTransition(
            revision_id=revision.id,
            from_task_id=source.id,
            to_task_id=target.id,
            condition=condition,
        )
        for source, target, condition in transitions
    )
    db.commit()
    return validate, review, archive, notify


def submit(
    db: Session,
    storage: LocalDocumentStorage,
    clock: TickingClock,
    *,
    metadata: RawInvoiceMetadata | None = None,
    mode: ExecutionMode = ExecutionMode.ORCHESTRATION,
    invoice_id: str = "invoice-1",
    run_id: str = "run-1",
    document: bytes | None = None,
    declared_media_type: str = "application/pdf",
) -> str:
    ids = iter((invoice_id, run_id))
    result = InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        storage,
        id_factory=ids.__next__,
        clock=clock,
    ).submit(
        InvoiceSubmission(
            metadata=metadata
            or RawInvoiceMetadata(
                "Supplier", "INV-001", "2026-08-13", "100.00", "EUR"
            ),
            original_filename="invoice.pdf",
            declared_media_type=declared_media_type,
            document=BytesIO(one_page_pdf() if document is None else document),
            mode=mode,
        )
    )
    return result.run_id


def compose(
    db: Session,
    storage: LocalDocumentStorage,
    clock: TickingClock,
    archive_task_id: int,
    archive_faults: tuple[TaskResult, ...] = (),
    run_id: str = "run-1",
) -> InvoiceExecutionCoordinator:
    effect_ids = iter(
        (f"archive-record-{run_id}", f"notification-{run_id}")
    )
    step_uow = SqlAlchemyAutomaticStepUnitOfWork(
        db,
        id_factory=effect_ids.__next__,
    )
    validation = DocumentValidationExecutor(step_uow, PypdfInspector(storage))
    archive = ArchiveDocumentExecutor(step_uow)
    if archive_faults:
        archive = DeterministicFaultExecutor(
            archive,
            DeterministicFaultSchedule(
                {FaultKey(run_id, archive_task_id): archive_faults}
            ),
        )
    notification = CreateNotificationExecutor(step_uow)
    automatic = AutomaticStepService(
        step_uow,
        AutomaticExecutorRegistry(
            {
                TaskType.DOCUMENT_VALIDATION: validation,
                TaskType.ARCHIVE_DOCUMENT: archive,
                TaskType.CREATE_NOTIFICATION: notification,
            }
        ),
        clock=clock,
        effect_policy=CompositeAutomaticStepEffectPolicy(
            (
                DocumentValidationEffectPolicy(step_uow),
                InvoiceBusinessEffectPolicy(step_uow),
            )
        ),
    )
    approval_ids = iter((f"work-item-{run_id}", f"decision-{run_id}"))
    approvals = HumanApprovalService(
        SqlAlchemyApprovalUnitOfWork(db),
        id_factory=approval_ids.__next__,
        clock=clock,
    )
    state_reader = SqlAlchemyRunControlReader(db)
    orchestrator = InvoiceOrchestrator(
        state_reader,
        automatic,
        approvals,
    )
    return InvoiceExecutionCoordinator(
        orchestrator,
        approvals,
        InvoiceChoreographer(
            state_reader,
            automatic,
            approvals,
            InMemoryRunEventBus(),
        ),
        state_reader,
    )


def trace_kinds(view) -> list[str]:
    return [item.kind for item in view.trace]


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_s1_approved_invoice_is_archived_and_notified(
    db: Session,
    tmp_path,
    mode: ExecutionMode,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    clock = TickingClock()
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit(db, storage, clock, mode=mode)
    coordinator = compose(db, storage, clock, archive.id)

    waiting = coordinator.drive(run_id)
    resumed = coordinator.decide_and_resume(
        waiting.work_item_id,
        ApprovalDecisionInput(ApprovalChoice.APPROVE, note="Approved"),
        expected_state_version=waiting.state_version,
    )
    terminal = resumed.execution
    view = SqlAlchemyInvoiceRunQueryService(db).get(run_id)
    invoice = db.get(Invoice, "invoice-1")

    assert waiting.phase is CursorPhase.WAITING_FOR_APPROVAL
    assert terminal.terminal_decision is TerminalDecision.SUCCESSFUL_TERMINAL
    assert view.invoice_state == "ARCHIVED"
    assert view.execution_mode is mode
    assert view.run_status == "COMPLETED"
    assert view.archive_document_identity == invoice.document_identity
    assert view.notification == "Invoice INV-001 was archived successfully."
    assert view.approval.decision == "APPROVE"
    assert trace_kinds(view).count("NOTIFICATION_CREATED") == 1


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_s2_rejected_invoice_skips_archive_and_notifies_reason(
    db: Session,
    tmp_path,
    mode: ExecutionMode,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    clock = TickingClock()
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit(db, storage, clock, mode=mode)
    coordinator = compose(db, storage, clock, archive.id)

    waiting = coordinator.drive(run_id)
    coordinator.decide_and_resume(
        waiting.work_item_id,
        ApprovalDecisionInput(
            ApprovalChoice.REJECT,
            reason="Amount does not match the purchase order",
        ),
        expected_state_version=waiting.state_version,
    )
    view = SqlAlchemyInvoiceRunQueryService(db).get(run_id)

    assert view.invoice_state == "REJECTED"
    assert view.execution_mode is mode
    assert view.run_status == "COMPLETED"
    assert view.archive_document_identity is None
    assert view.notification == "Invoice INV-001 was rejected."
    assert view.approval.reason == "Amount does not match the purchase order"
    assert db.scalar(select(func.count()).select_from(ArchiveRecord)) == 0


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_s3_invalid_invoice_has_no_approval_and_notifies_failure(
    db: Session,
    tmp_path,
    mode: ExecutionMode,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    clock = TickingClock()
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit(
        db,
        storage,
        clock,
        metadata=RawInvoiceMetadata(" ", "INV-001", "bad", "0", "eur"),
        mode=mode,
    )
    coordinator = compose(db, storage, clock, archive.id)

    terminal = coordinator.drive(run_id)
    view = SqlAlchemyInvoiceRunQueryService(db).get(run_id)

    assert terminal.phase is CursorPhase.TERMINAL
    assert view.invoice_state == "VALIDATION_FAILED"
    assert view.execution_mode is mode
    assert view.run_status == "COMPLETED"
    assert view.approval is None
    assert view.notification == (
        "Invoice invoice-1 failed document or metadata validation."
    )
    assert db.scalar(select(func.count()).select_from(ApprovalWorkItem)) == 0


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_s4_archive_retries_once_then_succeeds(
    db: Session,
    tmp_path,
    mode: ExecutionMode,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    clock = TickingClock()
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit(db, storage, clock, mode=mode)
    coordinator = compose(
        db,
        storage,
        clock,
        archive.id,
        (RETRYABLE_ARCHIVE_FAILURE,),
    )

    waiting = coordinator.drive(run_id)
    coordinator.decide_and_resume(
        waiting.work_item_id,
        ApprovalDecisionInput(ApprovalChoice.APPROVE),
        expected_state_version=waiting.state_version,
    )
    view = SqlAlchemyInvoiceRunQueryService(db).get(run_id)
    archive_attempts = db.scalar(
        select(func.count())
        .select_from(InvoiceTaskAttempt)
        .where(
            InvoiceTaskAttempt.run_id == run_id,
            InvoiceTaskAttempt.task_id == archive.id,
        )
    )

    assert view.invoice_state == "ARCHIVED"
    assert view.execution_mode is mode
    assert archive_attempts == 2
    assert trace_kinds(view).count("RETRY_OBSERVATION") == 1
    assert trace_kinds(view).count("NOTIFICATION_CREATED") == 1


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_s5_exhausted_archive_routes_to_manual_action_and_notification(
    db: Session,
    tmp_path,
    mode: ExecutionMode,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    clock = TickingClock()
    storage = LocalDocumentStorage(tmp_path)
    run_id = submit(db, storage, clock, mode=mode)
    coordinator = compose(
        db,
        storage,
        clock,
        archive.id,
        (RETRYABLE_ARCHIVE_FAILURE, RETRYABLE_ARCHIVE_FAILURE),
    )

    waiting = coordinator.drive(run_id)
    resumed = coordinator.decide_and_resume(
        waiting.work_item_id,
        ApprovalDecisionInput(ApprovalChoice.APPROVE),
        expected_state_version=waiting.state_version,
    )
    terminal = resumed.execution
    view = SqlAlchemyInvoiceRunQueryService(db).get(run_id)

    assert terminal.terminal_decision is TerminalDecision.SUCCESSFUL_TERMINAL
    assert view.invoice_state == "NEEDS_MANUAL_ACTION"
    assert view.execution_mode is mode
    assert view.run_status == "COMPLETED"
    assert view.archive_document_identity is None
    assert view.notification == (
        "Invoice INV-001 requires manual archive action."
    )
    assert trace_kinds(view).count("RETRY_OBSERVATION") == 1
    assert trace_kinds(view).count("INVOICE_STATE_CHANGED") == 3
    assert db.scalar(select(func.count()).select_from(ArchiveRecord)) == 0
    assert db.scalar(select(func.count()).select_from(InternalNotification)) == 1


INVOICE_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name.startswith("invoice_") or table.name == "invoices"
)


def _normalized_scenario_result(mode: ExecutionMode, scenario: str, root) -> tuple:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine, tables=INVOICE_TABLES)
    with Session(engine) as session:
        _validate, _review, archive, _notify = create_reference_revision(session)
        clock = TickingClock()
        storage = LocalDocumentStorage(root / mode.value)
        metadata = (
            RawInvoiceMetadata(" ", "INV-001", "bad", "0", "eur")
            if scenario == "invalid"
            else None
        )
        run_id = submit(session, storage, clock, metadata=metadata, mode=mode)
        faults: tuple[TaskResult, ...] = ()
        if scenario == "retry":
            faults = (RETRYABLE_ARCHIVE_FAILURE,)
        elif scenario == "manual":
            faults = (RETRYABLE_ARCHIVE_FAILURE, RETRYABLE_ARCHIVE_FAILURE)
        coordinator = compose(session, storage, clock, archive.id, faults)
        waiting_or_terminal = coordinator.drive(run_id)
        if scenario in {"approved", "retry", "manual"}:
            coordinator.decide_and_resume(
                waiting_or_terminal.work_item_id,
                ApprovalDecisionInput(ApprovalChoice.APPROVE, note="Approved"),
                expected_state_version=waiting_or_terminal.state_version,
            )
        elif scenario == "rejected":
            coordinator.decide_and_resume(
                waiting_or_terminal.work_item_id,
                ApprovalDecisionInput(
                    ApprovalChoice.REJECT,
                    reason="Amount does not match the purchase order",
                ),
                expected_state_version=waiting_or_terminal.state_version,
            )

        view = SqlAlchemyInvoiceRunQueryService(session).get(run_id)
        normalized_trace = tuple(
            (
                entry.kind,
                entry.task_id,
                entry.attempt_ordinal,
                (
                    entry.detail.split("; mode=", 1)[0]
                    if entry.detail and entry.kind == "RUN_STARTED"
                    else entry.detail
                ),
            )
            for entry in view.trace
        )
        return (
            view.invoice_state,
            view.run_status,
            (
                view.terminal_decision.value
                if view.terminal_decision is not None
                else None
            ),
            (
                (
                    view.approval.decision,
                    view.approval.note,
                    view.approval.reason,
                )
                if view.approval is not None
                else None
            ),
            view.archive_document_identity is not None,
            view.notification,
            normalized_trace,
        )


@pytest.mark.parametrize(
    "scenario",
    ("approved", "rejected", "invalid", "retry", "manual"),
)
def test_modes_have_normalized_business_and_trace_parity(
    tmp_path,
    scenario: str,
) -> None:
    orchestration = _normalized_scenario_result(
        ExecutionMode.ORCHESTRATION,
        scenario,
        tmp_path / scenario,
    )
    choreography = _normalized_scenario_result(
        ExecutionMode.CHOREOGRAPHY,
        scenario,
        tmp_path / scenario,
    )

    assert choreography == orchestration
