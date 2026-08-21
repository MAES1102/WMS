from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from time import perf_counter

import pytest
from pypdf import PdfWriter
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.persistence.database import Base
from app.domain.approval import ApprovalChoice, ApprovalDecisionInput
from app.domain.types import ExecutionMode
from app.application.invoice_validation import MAX_PDF_BYTES
from app.infrastructure.documents import DocumentBoundaryError, LocalDocumentStorage
from app.persistence.models import (
    ApprovalDecision,
    ApprovalWorkItem,
    ArchiveRecord,
    InternalNotification,
    Invoice,
    InvoiceTaskAttempt,
    InvoiceTraceEntry,
    InvoiceWorkflowRun,
    RevisionTask,
    WorkflowRevision,
)
from app.persistence.orchestration import SqlAlchemyInvoiceRunQueryService
from tests.persistence.test_invoice_orchestration import (
    TickingClock,
    INVOICE_TABLES,
    _normalized_scenario_result,
    compose,
    create_reference_revision,
    submit,
)


SCENARIOS = ("approved", "rejected", "invalid", "retry", "manual")
EXPECTED_TRACE_KINDS = {
    "approved": (
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "TRANSITION_SELECTED",
        "INVOICE_STATE_CHANGED",
        "WAITING_FOR_APPROVAL",
        "APPROVAL_DECIDED",
        "INVOICE_STATE_CHANGED",
        "RUN_RESUMED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "INVOICE_STATE_CHANGED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "NOTIFICATION_CREATED",
        "SUCCESSFUL_TERMINAL",
    ),
    "rejected": (
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "TRANSITION_SELECTED",
        "INVOICE_STATE_CHANGED",
        "WAITING_FOR_APPROVAL",
        "APPROVAL_DECIDED",
        "INVOICE_STATE_CHANGED",
        "RUN_RESUMED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "NOTIFICATION_CREATED",
        "SUCCESSFUL_TERMINAL",
    ),
    "invalid": (
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "INVOICE_STATE_CHANGED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "NOTIFICATION_CREATED",
        "SUCCESSFUL_TERMINAL",
    ),
    "retry": (
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "TRANSITION_SELECTED",
        "INVOICE_STATE_CHANGED",
        "WAITING_FOR_APPROVAL",
        "APPROVAL_DECIDED",
        "INVOICE_STATE_CHANGED",
        "RUN_RESUMED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "RETRY_OBSERVATION",
        "ATTEMPT_OUTCOME",
        "INVOICE_STATE_CHANGED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "NOTIFICATION_CREATED",
        "SUCCESSFUL_TERMINAL",
    ),
    "manual": (
        "RUN_STARTED",
        "ATTEMPT_OUTCOME",
        "TRANSITION_SELECTED",
        "INVOICE_STATE_CHANGED",
        "WAITING_FOR_APPROVAL",
        "APPROVAL_DECIDED",
        "INVOICE_STATE_CHANGED",
        "RUN_RESUMED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "RETRY_OBSERVATION",
        "ATTEMPT_OUTCOME",
        "INVOICE_STATE_CHANGED",
        "TRANSITION_SELECTED",
        "ATTEMPT_OUTCOME",
        "NOTIFICATION_CREATED",
        "SUCCESSFUL_TERMINAL",
    ),
}


def pdf_bytes(*, pages: int = 1, password: str | None = None) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    if password is not None:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def persistent_engine(database: Path):
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
        dbapi_connection.execute("PRAGMA busy_timeout=30000")

    return engine


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_equivalent_runs_repeat_the_normalized_trace(
    tmp_path,
    mode: ExecutionMode,
    scenario: str,
) -> None:
    first = _normalized_scenario_result(
        mode,
        scenario,
        tmp_path / "first",
    )
    second = _normalized_scenario_result(
        mode,
        scenario,
        tmp_path / "second",
    )

    assert second == first


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_retrieved_trace_is_complete_and_ordered(
    tmp_path,
    mode: ExecutionMode,
    scenario: str,
) -> None:
    result = _normalized_scenario_result(mode, scenario, tmp_path)
    trace = result[-1]

    assert tuple(item[0] for item in trace) == EXPECTED_TRACE_KINDS[scenario]


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_waiting_run_survives_restart_and_resumes_original_state(
    tmp_path,
    mode: ExecutionMode,
) -> None:
    database = tmp_path / f"restart-{mode.value}.db"
    storage = LocalDocumentStorage(tmp_path / f"documents-{mode.value}")
    engine = persistent_engine(database)
    Base.metadata.create_all(engine, tables=INVOICE_TABLES)

    with Session(engine) as first_session:
        _validate, _review, archive, _notify = create_reference_revision(
            first_session
        )
        clock = TickingClock()
        run_id = submit(first_session, storage, clock, mode=mode)
        waiting = compose(
            first_session,
            storage,
            clock,
            archive.id,
            run_id=run_id,
        ).drive(run_id)
        before = SqlAlchemyInvoiceRunQueryService(first_session).get(run_id)
        revision_id = first_session.get(InvoiceWorkflowRun, run_id).revision_id

        assert before.invoice_state == "PENDING_APPROVAL"
        assert before.run_status == "WAITING_FOR_APPROVAL"
        assert before.approval is None
        assert waiting.work_item_id is not None

    engine.dispose()

    restarted = persistent_engine(database)
    with Session(restarted) as second_session:
        restored = SqlAlchemyInvoiceRunQueryService(second_session).get(run_id)
        archive = second_session.scalars(
            select(RevisionTask).where(
                RevisionTask.revision_id == revision_id,
                RevisionTask.task_key == "archive",
            )
        ).one()
        coordinator = compose(
            second_session,
            storage,
            TickingClock(),
            archive.id,
            run_id=run_id,
        )

        assert restored.invoice_id == before.invoice_id
        assert restored.state_version == before.state_version
        assert tuple(item.kind for item in restored.trace) == tuple(
            item.kind for item in before.trace
        )

        coordinator.decide_and_resume(
            waiting.work_item_id,
            ApprovalDecisionInput(ApprovalChoice.APPROVE, note="After restart"),
            expected_state_version=restored.state_version,
        )
        completed = SqlAlchemyInvoiceRunQueryService(second_session).get(run_id)

        assert completed.invoice_state == "ARCHIVED"
        assert completed.run_status == "COMPLETED"
        assert completed.approval.note == "After restart"
        assert completed.archive_document_identity is not None
        assert completed.notification == "Invoice INV-001 was archived successfully."
        assert second_session.get(WorkflowRevision, revision_id) is not None
        assert second_session.get(Invoice, completed.invoice_id) is not None
        assert second_session.scalar(
            select(func.count())
            .select_from(InvoiceTaskAttempt)
            .where(InvoiceTaskAttempt.run_id == run_id)
        ) == 3
        assert second_session.scalar(
            select(func.count())
            .select_from(ApprovalDecision)
        ) == 1
        assert second_session.scalar(
            select(func.count()).select_from(ArchiveRecord)
        ) == 1
        assert second_session.scalar(
            select(func.count()).select_from(InternalNotification)
        ) == 1
        assert second_session.scalar(
            select(func.count())
            .select_from(InvoiceTraceEntry)
            .where(InvoiceTraceEntry.run_id == run_id)
        ) == len(completed.trace)
    restarted.dispose()


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
def test_two_interleaved_runs_preserve_state_partition(
    tmp_path,
    mode: ExecutionMode,
) -> None:
    engine = persistent_engine(tmp_path / f"concurrent-{mode.value}.db")
    storage = LocalDocumentStorage(tmp_path / f"concurrent-docs-{mode.value}")
    Base.metadata.create_all(engine, tables=INVOICE_TABLES)
    run_ids = ("run-a", "run-b")
    invoice_ids = ("invoice-a", "invoice-b")

    with Session(engine) as setup:
        _validate, _review, archive, _notify = create_reference_revision(setup)
        for invoice_id, run_id in zip(invoice_ids, run_ids, strict=True):
            submit(
                setup,
                storage,
                TickingClock(),
                mode=mode,
                invoice_id=invoice_id,
                run_id=run_id,
            )
        archive_task_id = archive.id

    def drive(run_id: str):
        with Session(engine) as session:
            return compose(
                session,
                storage,
                TickingClock(),
                archive_task_id,
                run_id=run_id,
            ).drive(run_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        waiting = tuple(pool.map(drive, run_ids))

    def decide(item) -> None:
        with Session(engine) as session:
            compose(
                session,
                storage,
                TickingClock(),
                archive_task_id,
                run_id=item.run_id,
            ).decide_and_resume(
                item.work_item_id,
                ApprovalDecisionInput(
                    ApprovalChoice.APPROVE,
                    note=f"Approved {item.run_id}",
                ),
                expected_state_version=item.state_version,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        tuple(pool.map(decide, waiting))

    with Session(engine) as check:
        views = {
            run_id: SqlAlchemyInvoiceRunQueryService(check).get(run_id)
            for run_id in run_ids
        }
        assert {view.invoice_id for view in views.values()} == set(invoice_ids)
        assert all(view.invoice_state == "ARCHIVED" for view in views.values())
        assert all(view.run_status == "COMPLETED" for view in views.values())
        assert views["run-a"].approval.note == "Approved run-a"
        assert views["run-b"].approval.note == "Approved run-b"
        assert (
            views["run-a"].archive_document_identity
            != views["run-b"].archive_document_identity
        )

        work_items = check.scalars(select(ApprovalWorkItem)).all()
        archives = check.scalars(select(ArchiveRecord)).all()
        notifications = check.scalars(select(InternalNotification)).all()
        assert {(item.run_id, item.invoice_id) for item in work_items} == set(
            zip(run_ids, invoice_ids, strict=True)
        )
        assert {(item.run_id, item.invoice_id) for item in archives} == set(
            zip(run_ids, invoice_ids, strict=True)
        )
        assert {(item.run_id, item.invoice_id) for item in notifications} == set(
            zip(run_ids, invoice_ids, strict=True)
        )
        for run_id in run_ids:
            positions = check.scalars(
                select(InvoiceTraceEntry.position)
                .where(InvoiceTraceEntry.run_id == run_id)
                .order_by(InvoiceTraceEntry.position)
            ).all()
            assert positions == list(range(1, len(positions) + 1))
    engine.dispose()


def test_completed_status_and_trace_reads_meet_reference_threshold(
    db: Session,
    tmp_path,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    storage = LocalDocumentStorage(tmp_path)
    clock = TickingClock()
    run_id = submit(db, storage, clock)
    coordinator = compose(db, storage, clock, archive.id, run_id=run_id)
    waiting = coordinator.drive(run_id)
    coordinator.decide_and_resume(
        waiting.work_item_id,
        ApprovalDecisionInput(ApprovalChoice.APPROVE),
        expected_state_version=waiting.state_version,
    )
    queries = SqlAlchemyInvoiceRunQueryService(db)
    expected = queries.get(run_id)

    durations = []
    for _ in range(100):
        started = perf_counter()
        observed = queries.get(run_id)
        durations.append(perf_counter() - started)
        assert observed == expected

    assert sum(duration < 1.0 for duration in durations) >= 95


@pytest.mark.parametrize("mode", tuple(ExecutionMode))
@pytest.mark.parametrize(
    "content, media_type, rejected_at_storage",
    (
        (b"", "application/pdf", True),
        (b"x" * (MAX_PDF_BYTES + 1), "application/pdf", True),
        (pdf_bytes(), "text/plain", False),
        (b"this is not a PDF", "application/pdf", False),
        (b"%PDF-1.7\nmalformed", "application/pdf", False),
        (pdf_bytes(pages=0), "application/pdf", False),
        (pdf_bytes(password="secret"), "application/pdf", False),
    ),
)
def test_every_pdf_boundary_prevents_human_approval(
    db: Session,
    tmp_path,
    mode: ExecutionMode,
    content: bytes,
    media_type: str,
    rejected_at_storage: bool,
) -> None:
    _validate, _review, archive, _notify = create_reference_revision(db)
    storage = LocalDocumentStorage(tmp_path)
    clock = TickingClock()

    if rejected_at_storage:
        with pytest.raises(DocumentBoundaryError):
            submit(
                db,
                storage,
                clock,
                mode=mode,
                document=content,
                declared_media_type=media_type,
            )
    else:
        run_id = submit(
            db,
            storage,
            clock,
            mode=mode,
            document=content,
            declared_media_type=media_type,
        )
        compose(
            db,
            storage,
            clock,
            archive.id,
            run_id=run_id,
        ).drive(run_id)
        view = SqlAlchemyInvoiceRunQueryService(db).get(run_id)
        assert view.invoice_state == "VALIDATION_FAILED"
        assert view.run_status == "COMPLETED"

    assert db.scalar(select(func.count()).select_from(ApprovalWorkItem)) == 0
