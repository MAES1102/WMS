"""Automatic validation task for structured Purchase Requests."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.application.ports import ExecutionContext, PurchaseRequestStateChanged, PurchaseRequestValidated, StepEffect, StepResolution
from app.domain.purchase_request import PurchaseRequestState, PurchaseRequestValidationError, RawPurchaseRequest, validate_purchase_request
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


@dataclass(frozen=True)
class PurchaseRequestValidationInput:
    request: RawPurchaseRequest
    submitted_on: date


class PurchaseRequestValidationSource(Protocol):
    def load(self, context: ExecutionContext) -> PurchaseRequestValidationInput: ...


class PurchaseRequestValidationExecutor:
    def __init__(self, source: PurchaseRequestValidationSource) -> None:
        self._source = source

    def execute(self, context: ExecutionContext) -> TaskResult:
        if context.task_type is not TaskType.REQUEST_VALIDATION:
            raise ValueError("PurchaseRequestValidationExecutor requires REQUEST_VALIDATION")
        value = self._source.load(context)
        try:
            validate_purchase_request(value.request, submitted_on=value.submitted_on)
        except PurchaseRequestValidationError as exc:
            return TaskResult(TaskOutcome.FAILURE, FailureClass.BUSINESS, str(exc))
        return TaskResult(TaskOutcome.SUCCESS)


class PurchaseRequestValidationEffectPolicy:
    def __init__(self, source: PurchaseRequestValidationSource) -> None:
        self._source = source

    def effects_for(self, context: ExecutionContext, result: TaskResult, _resolution: StepResolution | None = None) -> tuple[StepEffect, ...]:
        if context.task_type is not TaskType.REQUEST_VALIDATION:
            return ()
        if result.outcome is TaskOutcome.SUCCESS:
            value = self._source.load(context)
            return (PurchaseRequestValidated(validate_purchase_request(value.request, submitted_on=value.submitted_on)),)
        if result.failure_class is FailureClass.BUSINESS:
            return (PurchaseRequestStateChanged(PurchaseRequestState.VALIDATION_FAILED, result.reason),)
        return ()
