"""Business executors and effects for archive and final notification tasks."""

from dataclasses import dataclass
from typing import Protocol

from app.application.ports import (
    ArchiveRecordCreated,
    AutomaticStepEffectPolicy,
    ExecutionContext,
    InternalNotificationCreated,
    InvoiceStateChanged,
    RetryCurrentTask,
    StepEffect,
    StepResolution,
)
from app.domain.invoice import InvoiceState
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


_NOTIFIABLE_STATES = frozenset(
    {
        InvoiceState.VALIDATION_FAILED,
        InvoiceState.REJECTED,
        InvoiceState.ARCHIVED,
        InvoiceState.NEEDS_MANUAL_ACTION,
    }
)


@dataclass(frozen=True)
class InvoiceBusinessSnapshot:
    invoice_state: InvoiceState
    document_identity: str
    invoice_number: str | None


class InvoiceBusinessSource(Protocol):
    def load_business(self, context: ExecutionContext) -> InvoiceBusinessSnapshot:
        """Load the invoice data needed by bounded business executors."""


class ArchiveDocumentExecutor:
    """Validate that the current approved document is ready to be archived."""

    def __init__(self, source: InvoiceBusinessSource) -> None:
        self._source = source

    def execute(self, context: ExecutionContext) -> TaskResult:
        if context.task_type is not TaskType.ARCHIVE_DOCUMENT:
            raise ValueError("ArchiveDocumentExecutor requires ARCHIVE_DOCUMENT")
        snapshot = self._source.load_business(context)
        if snapshot.invoice_state is not InvoiceState.APPROVED:
            return TaskResult(
                TaskOutcome.FAILURE,
                FailureClass.BUSINESS,
                "invoice must be APPROVED before archiving",
            )
        if not snapshot.document_identity:
            return TaskResult(
                TaskOutcome.FAILURE,
                FailureClass.NON_RETRYABLE_TECHNICAL,
                "approved invoice has no controlled document identity",
            )
        return TaskResult(TaskOutcome.SUCCESS)


class CreateNotificationExecutor:
    """Allow one notification only after a meaningful final business state."""

    def __init__(self, source: InvoiceBusinessSource) -> None:
        self._source = source

    def execute(self, context: ExecutionContext) -> TaskResult:
        if context.task_type is not TaskType.CREATE_NOTIFICATION:
            raise ValueError(
                "CreateNotificationExecutor requires CREATE_NOTIFICATION"
            )
        snapshot = self._source.load_business(context)
        if snapshot.invoice_state not in _NOTIFIABLE_STATES:
            return TaskResult(
                TaskOutcome.FAILURE,
                FailureClass.BUSINESS,
                "invoice has no final business state to notify",
            )
        return TaskResult(TaskOutcome.SUCCESS)


class InvoiceBusinessEffectPolicy:
    """Translate archive/notification results into explicit atomic effects."""

    def __init__(self, source: InvoiceBusinessSource) -> None:
        self._source = source

    def effects_for(
        self,
        context: ExecutionContext,
        result: TaskResult,
        resolution: StepResolution | None = None,
    ) -> tuple[StepEffect, ...]:
        if context.task_type is TaskType.ARCHIVE_DOCUMENT:
            if result.outcome is TaskOutcome.SUCCESS:
                snapshot = self._source.load_business(context)
                return (
                    ArchiveRecordCreated(snapshot.document_identity),
                    InvoiceStateChanged(InvoiceState.ARCHIVED),
                )
            if not isinstance(resolution, RetryCurrentTask):
                return (
                    InvoiceStateChanged(
                        InvoiceState.NEEDS_MANUAL_ACTION,
                        result.reason,
                    ),
                )
            return ()

        if (
            context.task_type is TaskType.CREATE_NOTIFICATION
            and result.outcome is TaskOutcome.SUCCESS
        ):
            snapshot = self._source.load_business(context)
            return (
                InternalNotificationCreated(self._message(context, snapshot)),
            )
        return ()

    @staticmethod
    def _message(
        context: ExecutionContext,
        snapshot: InvoiceBusinessSnapshot,
    ) -> str:
        reference = snapshot.invoice_number or context.invoice_id
        messages = {
            InvoiceState.ARCHIVED: f"Invoice {reference} was archived successfully.",
            InvoiceState.REJECTED: f"Invoice {reference} was rejected.",
            InvoiceState.VALIDATION_FAILED: (
                f"Invoice {reference} failed document or metadata validation."
            ),
            InvoiceState.NEEDS_MANUAL_ACTION: (
                f"Invoice {reference} requires manual archive action."
            ),
        }
        try:
            return messages[snapshot.invoice_state]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported notification state {snapshot.invoice_state.value}"
            ) from exc


class CompositeAutomaticStepEffectPolicy:
    """Compose independent task-specific effect policies in stable order."""

    def __init__(
        self,
        policies: tuple[AutomaticStepEffectPolicy, ...],
    ) -> None:
        self._policies = tuple(policies)

    def effects_for(
        self,
        context: ExecutionContext,
        result: TaskResult,
        resolution: StepResolution | None = None,
    ) -> tuple[StepEffect, ...]:
        effects: list[StepEffect] = []
        for policy in self._policies:
            effects.extend(policy.effects_for(context, result, resolution))
        return tuple(effects)
