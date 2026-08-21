"""Application service for structured Purchase Request submission."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from app.domain.purchase_request import RawPurchaseRequest
from app.domain.types import DemoScenario, ExecutionMode


class SubmissionUnavailable(RuntimeError): pass
class SubmissionConflict(RuntimeError): pass


@dataclass(frozen=True)
class ActiveWorkflow:
    revision_id: int
    start_task_id: int


@dataclass(frozen=True)
class PurchaseRequestSubmission:
    request: RawPurchaseRequest
    mode: ExecutionMode = ExecutionMode.ORCHESTRATION
    scenario: DemoScenario = DemoScenario.STANDARD


@dataclass(frozen=True)
class CreateSubmission:
    purchase_request_id: str
    run_id: str
    revision_id: int
    start_task_id: int
    mode: ExecutionMode
    scenario: DemoScenario
    request: RawPurchaseRequest
    submitted_at: datetime


@dataclass(frozen=True)
class SubmissionCreated:
    purchase_request_id: str
    run_id: str
    state_version: int


class SubmissionUnitOfWork(Protocol):
    def load_active_workflow(self) -> ActiveWorkflow: ...
    def create_submission(self, command: CreateSubmission) -> None: ...


class PurchaseRequestSubmissionService:
    def __init__(self, unit_of_work: SubmissionUnitOfWork, id_factory: Callable[[], str] | None = None, clock: Callable[[], datetime] | None = None) -> None:
        self._unit_of_work = unit_of_work
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._clock = clock or (lambda: datetime.now(UTC))

    def submit(self, submission: PurchaseRequestSubmission) -> SubmissionCreated:
        mode = ExecutionMode(submission.mode)
        scenario = DemoScenario(submission.scenario)
        self._validate_transport_bounds(submission.request)
        workflow = self._unit_of_work.load_active_workflow()
        command = CreateSubmission(
            self._id_factory(), self._id_factory(), workflow.revision_id,
            workflow.start_task_id, mode, scenario, submission.request, self._clock()
        )
        self._unit_of_work.create_submission(command)
        return SubmissionCreated(command.purchase_request_id, command.run_id, 1)

    @staticmethod
    def _validate_transport_bounds(value: RawPurchaseRequest) -> None:
        bounds = {"requester_name": 512, "department": 512, "item_or_service": 1024,
                  "supplier": 512, "amount": 32, "currency": 16,
                  "business_justification": 2000, "required_date": 32}
        for field, maximum in bounds.items():
            raw = getattr(value, field)
            if not isinstance(raw, str) or len(raw) > maximum:
                raise ValueError(f"{field} must be text of at most {maximum} characters")
