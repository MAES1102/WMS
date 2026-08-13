import pytest

from app.domain.types import (
    TaskDefinition,
    TaskType,
    TransitionCondition,
    TransitionDefinition,
    WorkflowDefinition,
)
from app.domain.validation import (
    WorkflowDefinitionError,
    validate_workflow_definition,
)


def _definition(*tasks: TaskDefinition) -> WorkflowDefinition:
    transitions = tuple(
        TransitionDefinition(
            id=index,
            from_task_id=source.id,
            to_task_id=target.id,
            condition=TransitionCondition.SUCCESS,
        )
        for index, (source, target) in enumerate(zip(tasks, tasks[1:]), start=1)
    )
    return WorkflowDefinition(id=1, tasks=tasks, transitions=transitions)


def test_reference_task_catalog_and_bounds_are_accepted() -> None:
    definition = _definition(
        TaskDefinition(1, "Validate", TaskType.DOCUMENT_VALIDATION, True, 1),
        TaskDefinition(2, "Approve", TaskType.HUMAN_APPROVAL, False, None),
        TaskDefinition(3, "Archive", TaskType.ARCHIVE_DOCUMENT, False, 2),
        TaskDefinition(4, "Notify", TaskType.CREATE_NOTIFICATION, False, 1),
    )

    validate_workflow_definition(definition)


@pytest.mark.parametrize("max_attempts", [None, 0, -1, True])
def test_automatic_task_requires_positive_integer_bound(
    max_attempts: object,
) -> None:
    definition = _definition(
        TaskDefinition(
            1,
            "Validate",
            TaskType.DOCUMENT_VALIDATION,
            True,
            max_attempts,  # type: ignore[arg-type]
        )
    )

    with pytest.raises(WorkflowDefinitionError) as raised:
        validate_workflow_definition(definition)

    assert any(issue.rule == "FR-021" for issue in raised.value.issues)


def test_human_task_does_not_require_attempt_bound() -> None:
    definition = _definition(
        TaskDefinition(1, "Approve", TaskType.HUMAN_APPROVAL, True, None)
    )

    validate_workflow_definition(definition)


def test_unsupported_task_type_is_rejected() -> None:
    definition = _definition(
        TaskDefinition(
            1,
            "Unknown",
            "SEND_EMAIL",  # type: ignore[arg-type]
            True,
            1,
        )
    )

    with pytest.raises(WorkflowDefinitionError) as raised:
        validate_workflow_definition(definition)

    assert [(issue.rule, issue.detail) for issue in raised.value.issues] == [
        ("FR-049", "Task 1 ('Unknown') has unsupported task_type='SEND_EMAIL'")
    ]
