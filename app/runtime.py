"""Composition root for the purchase_request-approval application."""

import os
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.approval import HumanApprovalService
from app.application.choreography import PurchaseRequestChoreographer
from app.application.constructor import WorkflowConstructorService
from app.application.executors import (
    AuthorizationDemoFaultExecutor,
    AutomaticExecutorRegistry,
)
from app.application.purchase_request_tasks import (
    PurchaseAuthorizationExecutor,
    CreateNotificationExecutor,
    PurchaseRequestBusinessEffectPolicy,
)
from app.application.purchase_request_validation import (
    PurchaseRequestValidationEffectPolicy,
    PurchaseRequestValidationExecutor,
)
from app.application.orchestration import (
    PurchaseRequestExecutionCoordinator,
    PurchaseRequestOrchestrator,
    PurchaseRequestRunQueryService,
)
from app.application.ports import ExecutionContext, StepEffect, StepResolution
from app.application.step_service import AutomaticStepService
from app.application.submission import PurchaseRequestSubmissionService
from app.domain.types import DemoScenario, TaskResult, TaskType
from app.infrastructure.event_bus import InMemoryRunEventBus
from app.persistence.approval import (
    SqlAlchemyApprovalQueryService,
    SqlAlchemyApprovalUnitOfWork,
)
from app.persistence.bootstrap import (
    create_purchase_request_schema,
    ensure_reference_workflow,
)
from app.persistence.constructor import SqlAlchemyWorkflowConstructorRepository
from app.persistence.orchestration import (
    SqlAlchemyPurchaseRequestRunQueryService,
    SqlAlchemyRunControlReader,
)
from app.persistence.models import PurchaseRequestWorkflowRun
from app.persistence.step import SqlAlchemyAutomaticStepUnitOfWork
from app.persistence.submission import SqlAlchemySubmissionUnitOfWork


WORKFLOW_DATABASE_URL = os.getenv(
    "WORKFLOW_DATABASE_URL",
    "sqlite:///./workflow.db",
)

_engine_options: dict = {"connect_args": {"check_same_thread": False}}
if WORKFLOW_DATABASE_URL in {"sqlite://", "sqlite:///:memory:"}:
    _engine_options["poolclass"] = StaticPool

purchase_request_engine = create_engine(WORKFLOW_DATABASE_URL, **_engine_options)


@event.listens_for(purchase_request_engine, "connect")
def _enable_purchase_request_foreign_keys(dbapi_connection, _connection_record) -> None:
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


PurchaseRequestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=purchase_request_engine,
)
purchase_request_event_bus = InMemoryRunEventBus()


def initialize_purchase_request_runtime() -> None:
    create_purchase_request_schema(purchase_request_engine)
    with PurchaseRequestSessionLocal() as session:
        ensure_reference_workflow(session)


def get_purchase_request_db() -> Generator[Session, None, None]:
    session = PurchaseRequestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_submission_service(
    db: Session = Depends(get_purchase_request_db),
) -> PurchaseRequestSubmissionService:
    return PurchaseRequestSubmissionService(SqlAlchemySubmissionUnitOfWork(db))


def get_approval_queries(
    db: Session = Depends(get_purchase_request_db),
) -> SqlAlchemyApprovalQueryService:
    return SqlAlchemyApprovalQueryService(db)


def get_run_queries(
    db: Session = Depends(get_purchase_request_db),
) -> PurchaseRequestRunQueryService:
    return SqlAlchemyPurchaseRequestRunQueryService(db)


def get_constructor_service(
    db: Session = Depends(get_purchase_request_db),
) -> WorkflowConstructorService:
    return WorkflowConstructorService(
        SqlAlchemyWorkflowConstructorRepository(db)
    )


class _PurchaseRequestStepEffects:
    """Validation effects, then business effects, for one purchase_request step."""

    def __init__(
        self,
        validation: PurchaseRequestValidationEffectPolicy,
        business: PurchaseRequestBusinessEffectPolicy,
    ) -> None:
        self._validation = validation
        self._business = business

    def effects_for(
        self,
        context: ExecutionContext,
        result: TaskResult,
        resolution: StepResolution | None = None,
    ) -> tuple[StepEffect, ...]:
        return self._validation.effects_for(
            context, result, resolution
        ) + self._business.effects_for(context, result, resolution)


def get_execution_coordinator(
    db: Session = Depends(get_purchase_request_db),
) -> PurchaseRequestExecutionCoordinator:
    step_uow = SqlAlchemyAutomaticStepUnitOfWork(db)

    def scenario_for_run(run_id: str) -> DemoScenario:
        run = db.get(PurchaseRequestWorkflowRun, run_id)
        if run is None:
            raise ValueError(f"Run {run_id!r} does not exist")
        return DemoScenario(run.scenario)

    registry = AutomaticExecutorRegistry(
        {
            TaskType.REQUEST_VALIDATION: PurchaseRequestValidationExecutor(step_uow),
            TaskType.PURCHASE_AUTHORIZATION: AuthorizationDemoFaultExecutor(
                PurchaseAuthorizationExecutor(step_uow),
                scenario_for_run,
            ),
            TaskType.CREATE_NOTIFICATION: CreateNotificationExecutor(step_uow),
        }
    )
    automatic_steps = AutomaticStepService(
        step_uow,
        registry,
        effect_policy=_PurchaseRequestStepEffects(
            PurchaseRequestValidationEffectPolicy(step_uow),
            PurchaseRequestBusinessEffectPolicy(step_uow),
        ),
    )
    approvals = HumanApprovalService(SqlAlchemyApprovalUnitOfWork(db))
    state_reader = SqlAlchemyRunControlReader(db)
    return PurchaseRequestExecutionCoordinator(
        PurchaseRequestOrchestrator(
            state_reader,
            automatic_steps,
            approvals,
        ),
        approvals,
        PurchaseRequestChoreographer(
            state_reader,
            automatic_steps,
            approvals,
            purchase_request_event_bus,
        ),
        state_reader,
    )
