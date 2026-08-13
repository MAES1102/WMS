"""Pure retry policy applied before transition resolution."""

from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


def should_retry(
    *,
    task_type: TaskType,
    result: TaskResult,
    completed_attempts: int,
    max_attempts: int | None,
) -> bool:
    """Return whether the current automatic task must run again (FR-022)."""
    try:
        normalized_type = TaskType(task_type)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsupported task type {task_type!r}") from exc

    if completed_attempts < 1:
        raise ValueError("completed_attempts must be at least 1")

    if not normalized_type.is_automatic:
        return False

    if (
        not isinstance(max_attempts, int)
        or isinstance(max_attempts, bool)
        or max_attempts < 1
    ):
        raise ValueError("automatic task max_attempts must be a positive integer")

    return (
        result.outcome is TaskOutcome.FAILURE
        and result.failure_class is FailureClass.RETRYABLE_TECHNICAL
        and completed_attempts < max_attempts
    )
