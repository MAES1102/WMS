"""Composition root for the visible invoice-approval runtime."""

import os
from collections.abc import Generator
from pathlib import Path

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.approval import HumanApprovalService
from app.application.choreography import InvoiceChoreographer
from app.application.constructor import WorkflowConstructorService
from app.application.executors import AutomaticExecutorRegistry
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
    InvoiceExecutionCoordinator,
    InvoiceOrchestrator,
    InvoiceRunQueryService,
)
from app.application.step_service import AutomaticStepService
from app.application.submission import InvoiceSubmissionService
from app.domain.types import TaskType
from app.infrastructure.documents import LocalDocumentStorage
from app.infrastructure.event_bus import InMemoryRunEventBus
from app.infrastructure.pdf import PypdfInspector
from app.persistence.approval import (
    SqlAlchemyApprovalQueryService,
    SqlAlchemyApprovalUnitOfWork,
)
from app.persistence.bootstrap import (
    create_invoice_schema,
    ensure_reference_workflow,
)
from app.persistence.constructor import SqlAlchemyWorkflowConstructorRepository
from app.persistence.orchestration import (
    SqlAlchemyInvoiceRunQueryService,
    SqlAlchemyRunControlReader,
)
from app.persistence.step import SqlAlchemyAutomaticStepUnitOfWork
from app.persistence.submission import SqlAlchemySubmissionUnitOfWork


INVOICE_DATABASE_URL = os.getenv(
    "INVOICE_DATABASE_URL",
    "sqlite:///./invoice_v3.db",
)

_engine_options: dict = {"connect_args": {"check_same_thread": False}}
if INVOICE_DATABASE_URL in {"sqlite://", "sqlite:///:memory:"}:
    _engine_options["poolclass"] = StaticPool

invoice_engine = create_engine(INVOICE_DATABASE_URL, **_engine_options)


@event.listens_for(invoice_engine, "connect")
def _enable_invoice_foreign_keys(dbapi_connection, _connection_record) -> None:
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


InvoiceSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=invoice_engine,
)
invoice_storage = LocalDocumentStorage(
    Path(os.getenv("INVOICE_STORAGE_ROOT", "./invoice_documents"))
)
invoice_event_bus = InMemoryRunEventBus()


def initialize_invoice_runtime() -> None:
    create_invoice_schema(invoice_engine)
    with InvoiceSessionLocal() as session:
        ensure_reference_workflow(session)


def get_invoice_db() -> Generator[Session, None, None]:
    session = InvoiceSessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_submission_service(
    db: Session = Depends(get_invoice_db),
) -> InvoiceSubmissionService:
    return InvoiceSubmissionService(
        SqlAlchemySubmissionUnitOfWork(db),
        invoice_storage,
    )


def get_approval_service(
    db: Session = Depends(get_invoice_db),
) -> HumanApprovalService:
    return HumanApprovalService(SqlAlchemyApprovalUnitOfWork(db))


def get_approval_queries(
    db: Session = Depends(get_invoice_db),
) -> SqlAlchemyApprovalQueryService:
    return SqlAlchemyApprovalQueryService(db)


def get_run_queries(
    db: Session = Depends(get_invoice_db),
) -> InvoiceRunQueryService:
    return SqlAlchemyInvoiceRunQueryService(db)


def get_constructor_service(
    db: Session = Depends(get_invoice_db),
) -> WorkflowConstructorService:
    return WorkflowConstructorService(
        SqlAlchemyWorkflowConstructorRepository(db)
    )


def get_execution_coordinator(
    db: Session = Depends(get_invoice_db),
) -> InvoiceExecutionCoordinator:
    step_uow = SqlAlchemyAutomaticStepUnitOfWork(db)
    registry = AutomaticExecutorRegistry(
        {
            TaskType.DOCUMENT_VALIDATION: DocumentValidationExecutor(
                step_uow,
                PypdfInspector(invoice_storage),
            ),
            TaskType.ARCHIVE_DOCUMENT: ArchiveDocumentExecutor(step_uow),
            TaskType.CREATE_NOTIFICATION: CreateNotificationExecutor(step_uow),
        }
    )
    automatic_steps = AutomaticStepService(
        step_uow,
        registry,
        effect_policy=CompositeAutomaticStepEffectPolicy(
            (
                DocumentValidationEffectPolicy(step_uow),
                InvoiceBusinessEffectPolicy(step_uow),
            )
        ),
    )
    approvals = HumanApprovalService(SqlAlchemyApprovalUnitOfWork(db))
    state_reader = SqlAlchemyRunControlReader(db)
    return InvoiceExecutionCoordinator(
        InvoiceOrchestrator(
            state_reader,
            automatic_steps,
            approvals,
        ),
        approvals,
        InvoiceChoreographer(
            state_reader,
            automatic_steps,
            approvals,
            invoice_event_bus,
        ),
        state_reader,
    )
