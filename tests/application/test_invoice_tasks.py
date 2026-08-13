from app.application.invoice_tasks import (
    ArchiveDocumentExecutor,
    CompositeAutomaticStepEffectPolicy,
    CreateNotificationExecutor,
    InvoiceBusinessEffectPolicy,
    InvoiceBusinessSnapshot,
)
from app.application.ports import (
    ArchiveRecordCreated,
    ExecutionContext,
    InternalNotificationCreated,
    InvoiceStateChanged,
    RetryCurrentTask,
)
from app.domain.invoice import InvoiceState
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


class Source:
    def __init__(self, state: InvoiceState) -> None:
        self.snapshot = InvoiceBusinessSnapshot(state, "document-1", "INV-1")

    def load_business(self, _context):
        return self.snapshot


def context(task_type: TaskType, attempt: int = 1) -> ExecutionContext:
    return ExecutionContext("run-1", "invoice-1", 7, task_type, attempt)


def test_archive_success_preserves_identity_and_changes_state() -> None:
    source = Source(InvoiceState.APPROVED)
    ctx = context(TaskType.ARCHIVE_DOCUMENT)
    result = ArchiveDocumentExecutor(source).execute(ctx)

    effects = InvoiceBusinessEffectPolicy(source).effects_for(ctx, result)

    assert result == TaskResult(TaskOutcome.SUCCESS)
    assert effects == (
        ArchiveRecordCreated("document-1"),
        InvoiceStateChanged(InvoiceState.ARCHIVED),
    )


def test_archive_failure_changes_state_only_after_retry_is_exhausted() -> None:
    policy = InvoiceBusinessEffectPolicy(Source(InvoiceState.APPROVED))
    failure = TaskResult(
        TaskOutcome.FAILURE,
        FailureClass.RETRYABLE_TECHNICAL,
        "archive unavailable",
    )

    retry_effects = policy.effects_for(
        context(TaskType.ARCHIVE_DOCUMENT),
        failure,
        RetryCurrentTask(7, 2),
    )
    final_effects = policy.effects_for(
        context(TaskType.ARCHIVE_DOCUMENT, 2),
        failure,
    )

    assert retry_effects == ()
    assert final_effects == (
        InvoiceStateChanged(
            InvoiceState.NEEDS_MANUAL_ACTION,
            "archive unavailable",
        ),
    )


def test_notification_describes_the_persisted_final_state() -> None:
    source = Source(InvoiceState.NEEDS_MANUAL_ACTION)
    ctx = context(TaskType.CREATE_NOTIFICATION)
    result = CreateNotificationExecutor(source).execute(ctx)

    effects = InvoiceBusinessEffectPolicy(source).effects_for(ctx, result)

    assert result == TaskResult(TaskOutcome.SUCCESS)
    assert effects == (
        InternalNotificationCreated(
            "Invoice INV-1 requires manual archive action."
        ),
    )


def test_business_executors_reject_wrong_state_or_task_type() -> None:
    source = Source(InvoiceState.SUBMITTED)
    result = CreateNotificationExecutor(source).execute(
        context(TaskType.CREATE_NOTIFICATION)
    )
    assert result.outcome is TaskOutcome.FAILURE
    assert result.failure_class is FailureClass.BUSINESS

    try:
        ArchiveDocumentExecutor(source).execute(
            context(TaskType.DOCUMENT_VALIDATION)
        )
    except ValueError as exc:
        assert "requires ARCHIVE_DOCUMENT" in str(exc)
    else:
        raise AssertionError("wrong task type must be rejected")


def test_composite_policy_keeps_component_order() -> None:
    class EmptyPolicy:
        def effects_for(self, _context, _result, _resolution=None):
            return ()

    source = Source(InvoiceState.ARCHIVED)
    policy = CompositeAutomaticStepEffectPolicy(
        (EmptyPolicy(), InvoiceBusinessEffectPolicy(source))
    )
    effects = policy.effects_for(
        context(TaskType.CREATE_NOTIFICATION),
        TaskResult(TaskOutcome.SUCCESS),
    )
    assert isinstance(effects[0], InternalNotificationCreated)
