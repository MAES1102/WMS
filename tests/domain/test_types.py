import pytest

from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


def test_task_catalog_marks_only_human_approval_as_non_automatic() -> None:
    automatic = {task_type for task_type in TaskType if task_type.is_automatic}

    assert automatic == {
        TaskType.DOCUMENT_VALIDATION,
        TaskType.ARCHIVE_DOCUMENT,
        TaskType.CREATE_NOTIFICATION,
    }
    assert not TaskType.HUMAN_APPROVAL.is_automatic


def test_task_result_normalizes_controlled_string_values() -> None:
    result = TaskResult(
        outcome="FAILURE",  # type: ignore[arg-type]
        failure_class="BUSINESS",  # type: ignore[arg-type]
        reason="invalid invoice amount",
    )

    assert result.outcome is TaskOutcome.FAILURE
    assert result.failure_class is FailureClass.BUSINESS


def test_success_cannot_carry_failure_class() -> None:
    with pytest.raises(ValueError, match="successful task result"):
        TaskResult(
            outcome=TaskOutcome.SUCCESS,
            failure_class=FailureClass.BUSINESS,
        )


def test_failure_requires_failure_class() -> None:
    with pytest.raises(ValueError, match="failed task result"):
        TaskResult(outcome=TaskOutcome.FAILURE)


@pytest.mark.parametrize("outcome", ["UNKNOWN", None, 7])
def test_unsupported_outcome_is_rejected(outcome: object) -> None:
    with pytest.raises(ValueError, match="Unsupported task outcome"):
        TaskResult(outcome=outcome)  # type: ignore[arg-type]
