import pytest

from app.domain.retry import should_retry
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


def _failure(failure_class: FailureClass) -> TaskResult:
    return TaskResult(TaskOutcome.FAILURE, failure_class, "controlled failure")


@pytest.mark.parametrize(
    ("result", "completed_attempts", "expected"),
    [
        (_failure(FailureClass.RETRYABLE_TECHNICAL), 1, True),
        (_failure(FailureClass.RETRYABLE_TECHNICAL), 2, False),
        (_failure(FailureClass.BUSINESS), 1, False),
        (_failure(FailureClass.NON_RETRYABLE_TECHNICAL), 1, False),
        (TaskResult(TaskOutcome.SUCCESS), 1, False),
    ],
)
def test_retry_requires_retryable_failure_below_bound(
    result: TaskResult,
    completed_attempts: int,
    expected: bool,
) -> None:
    assert (
        should_retry(
            task_type=TaskType.ARCHIVE_DOCUMENT,
            result=result,
            completed_attempts=completed_attempts,
            max_attempts=2,
        )
        is expected
    )


def test_human_approval_is_never_automatically_retried() -> None:
    assert not should_retry(
        task_type=TaskType.HUMAN_APPROVAL,
        result=_failure(FailureClass.RETRYABLE_TECHNICAL),
        completed_attempts=1,
        max_attempts=None,
    )


@pytest.mark.parametrize("completed_attempts", [0, -1])
def test_completed_attempt_count_must_include_current_attempt(
    completed_attempts: int,
) -> None:
    with pytest.raises(ValueError, match="completed_attempts"):
        should_retry(
            task_type=TaskType.DOCUMENT_VALIDATION,
            result=_failure(FailureClass.RETRYABLE_TECHNICAL),
            completed_attempts=completed_attempts,
            max_attempts=2,
        )


@pytest.mark.parametrize("max_attempts", [None, 0, -1, True])
def test_automatic_task_requires_positive_integer_bound(
    max_attempts: object,
) -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        should_retry(
            task_type=TaskType.DOCUMENT_VALIDATION,
            result=_failure(FailureClass.RETRYABLE_TECHNICAL),
            completed_attempts=1,
            max_attempts=max_attempts,  # type: ignore[arg-type]
        )
