"""Safe automatic business tasks for Purchase Request Approval."""

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from app.application.ports import ExecutionContext, InternalNotificationCreated, PurchaseAuthorizationCreated, PurchaseRequestStateChanged, RetryCurrentTask, StepEffect, StepResolution
from app.domain.purchase_request import PurchaseRequestState
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


@dataclass(frozen=True)
class PurchaseRequestBusinessSnapshot:
    state: PurchaseRequestState
    item_or_service: str | None
    amount: str
    currency: str


class PurchaseRequestBusinessSource(Protocol):
    def load_business(self, context: ExecutionContext) -> PurchaseRequestBusinessSnapshot: ...


class PurchaseAuthorizationExecutor:
    def __init__(self, source: PurchaseRequestBusinessSource) -> None:
        self._source = source

    def execute(self, context: ExecutionContext) -> TaskResult:
        if context.task_type is not TaskType.PURCHASE_AUTHORIZATION:
            raise ValueError("PurchaseAuthorizationExecutor requires PURCHASE_AUTHORIZATION")
        if self._source.load_business(context).state is not PurchaseRequestState.APPROVED:
            return TaskResult(TaskOutcome.FAILURE, FailureClass.BUSINESS, "purchase request must be APPROVED before authorization")
        return TaskResult(TaskOutcome.SUCCESS)


class CreateNotificationExecutor:
    def __init__(self, source: PurchaseRequestBusinessSource) -> None:
        self._source = source

    def execute(self, context: ExecutionContext) -> TaskResult:
        allowed = {PurchaseRequestState.VALIDATION_FAILED, PurchaseRequestState.REJECTED, PurchaseRequestState.AUTHORIZED, PurchaseRequestState.NEEDS_MANUAL_ACTION}
        if context.task_type is not TaskType.CREATE_NOTIFICATION:
            raise ValueError("CreateNotificationExecutor requires CREATE_NOTIFICATION")
        if self._source.load_business(context).state not in allowed:
            return TaskResult(TaskOutcome.FAILURE, FailureClass.BUSINESS, "request has no final business state")
        return TaskResult(TaskOutcome.SUCCESS)


class PurchaseRequestBusinessEffectPolicy:
    def __init__(self, source: PurchaseRequestBusinessSource) -> None:
        self._source = source

    def effects_for(self, context: ExecutionContext, result: TaskResult, resolution: StepResolution | None = None) -> tuple[StepEffect, ...]:
        if context.task_type is TaskType.PURCHASE_AUTHORIZATION:
            if result.outcome is TaskOutcome.SUCCESS:
                return (PurchaseAuthorizationCreated(str(uuid4())), PurchaseRequestStateChanged(PurchaseRequestState.AUTHORIZED))
            if not isinstance(resolution, RetryCurrentTask):
                return (PurchaseRequestStateChanged(PurchaseRequestState.NEEDS_MANUAL_ACTION, result.reason),)
        if context.task_type is TaskType.CREATE_NOTIFICATION and result.outcome is TaskOutcome.SUCCESS:
            value = self._source.load_business(context)
            messages = {
                PurchaseRequestState.AUTHORIZED: "Purchase request was authorized internally.",
                PurchaseRequestState.REJECTED: "Purchase request was rejected.",
                PurchaseRequestState.VALIDATION_FAILED: "Purchase request failed validation.",
                PurchaseRequestState.NEEDS_MANUAL_ACTION: "Purchase request requires manual authorization action.",
            }
            return (InternalNotificationCreated(messages[value.state]),)
        return ()
