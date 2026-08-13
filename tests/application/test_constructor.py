from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.application.constructor import (
    DraftTaskSpec,
    DraftTransitionSpec,
    StoredWorkflowDraft,
    StoredWorkflowRevision,
    WorkflowActivationRejected,
    WorkflowConstructorService,
    WorkflowDraftRejected,
    WorkflowDraftSpec,
)


def valid_spec() -> WorkflowDraftSpec:
    return WorkflowDraftSpec(
        "Invoice approval",
        (
            DraftTaskSpec("validate", "Validate", "DOCUMENT_VALIDATION", True, 1),
            DraftTaskSpec("review", "Review", "HUMAN_APPROVAL", False, None),
            DraftTaskSpec("notify", "Notify", "CREATE_NOTIFICATION", False, 1),
        ),
        (
            DraftTransitionSpec("validate", "review", "SUCCESS"),
            DraftTransitionSpec("validate", "notify", "FAILURE"),
            DraftTransitionSpec("review", "notify", "SUCCESS"),
            DraftTransitionSpec("review", "notify", "FAILURE"),
        ),
    )


class FakeRepository:
    def __init__(self) -> None:
        self.value: StoredWorkflowDraft | None = None
        self.revision: StoredWorkflowRevision | None = None

    def list_drafts(self):
        return () if self.value is None else (self.value,)

    def get_draft(self, draft_id):
        if self.value is None or self.value.id != draft_id:
            raise LookupError
        return self.value

    def create_draft(self, spec, now):
        self.value = StoredWorkflowDraft(1, spec, now, now, None)
        return self.value

    def replace_draft(self, draft_id, spec, now):
        current = self.get_draft(draft_id)
        self.value = replace(current, spec=spec, updated_at=now)
        return self.value

    def delete_draft(self, draft_id):
        self.get_draft(draft_id)
        self.value = None

    def activate_draft(self, draft_id, now):
        current = self.get_draft(draft_id)
        self.revision = StoredWorkflowRevision(9, draft_id, 1, current.spec, now)
        return self.revision

    def get_revision(self, revision_id):
        assert self.revision is not None and self.revision.id == revision_id
        return self.revision


def service(repository: FakeRepository) -> WorkflowConstructorService:
    return WorkflowConstructorService(
        repository,
        clock=lambda: datetime(2026, 8, 13, 16, 0, tzinfo=UTC),
    )


def test_valid_bounded_definition_can_be_saved_and_activated() -> None:
    repository = FakeRepository()
    constructor = service(repository)

    draft = constructor.create_draft(valid_spec())
    revision = constructor.activate_draft(draft.id)

    assert draft.validation.valid
    assert revision.revision_number == 1
    assert revision.spec.tasks[1].max_attempts is None


def test_incomplete_graph_is_saved_but_cannot_be_activated() -> None:
    repository = FakeRepository()
    constructor = service(repository)
    incomplete = replace(
        valid_spec(),
        tasks=tuple(replace(task, is_start=False) for task in valid_spec().tasks),
    )

    draft = constructor.create_draft(incomplete)

    assert not draft.validation.valid
    assert any(issue.rule == "FR-002" for issue in draft.validation.issues)
    with pytest.raises(WorkflowActivationRejected) as rejected:
        constructor.activate_draft(draft.id)
    assert any(issue.rule == "FR-002" for issue in rejected.value.issues)
    assert repository.revision is None


@pytest.mark.parametrize(
    "invalid_spec, expected_rule",
    (
        (
            replace(
                valid_spec(),
                tasks=tuple(
                    replace(task, is_start=False) for task in valid_spec().tasks
                ),
            ),
            "FR-002",
        ),
        (
            WorkflowDraftSpec(
                "No terminal",
                valid_spec().tasks[:2],
                (
                    DraftTransitionSpec("validate", "review", "SUCCESS"),
                    DraftTransitionSpec("review", "validate", "SUCCESS"),
                ),
            ),
            "FR-003",
        ),
        (
            replace(
                valid_spec(),
                tasks=valid_spec().tasks
                + (
                    DraftTaskSpec(
                        "orphan",
                        "Unreachable notification",
                        "CREATE_NOTIFICATION",
                        False,
                        1,
                    ),
                ),
            ),
            "FR-004",
        ),
        (
            WorkflowDraftSpec(
                "Directed cycle",
                valid_spec().tasks[:2],
                (
                    DraftTransitionSpec("validate", "review", "SUCCESS"),
                    DraftTransitionSpec("review", "validate", "SUCCESS"),
                ),
            ),
            "FR-005",
        ),
    ),
)
def test_activation_validation_covers_every_graph_class_without_revision(
    invalid_spec: WorkflowDraftSpec,
    expected_rule: str,
) -> None:
    repository = FakeRepository()
    constructor = service(repository)
    draft = constructor.create_draft(invalid_spec)

    with pytest.raises(WorkflowActivationRejected) as rejected:
        constructor.activate_draft(draft.id)

    assert any(issue.rule == expected_rule for issue in rejected.value.issues)
    assert repository.revision is None


@pytest.mark.parametrize(
    "bad_spec, rule",
    (
        (
            replace(
                valid_spec(),
                tasks=(
                    replace(
                        valid_spec().tasks[0],
                        task_type="PYTHON_SCRIPT",
                    ),
                )
                + valid_spec().tasks[1:],
            ),
            "FR-049",
        ),
        (
            replace(
                valid_spec(),
                tasks=(
                    valid_spec().tasks[0],
                    replace(valid_spec().tasks[1], max_attempts=3),
                    valid_spec().tasks[2],
                ),
            ),
            "FR-050",
        ),
        (
            replace(
                valid_spec(),
                transitions=valid_spec().transitions
                + (DraftTransitionSpec("validate", "notify", "SUCCESS"),),
            ),
            "FR-010",
        ),
        (
            replace(
                valid_spec(),
                transitions=(
                    DraftTransitionSpec("validate", "review", "MAYBE"),
                )
                + valid_spec().transitions[1:],
            ),
            "FR-007",
        ),
        (
            replace(
                valid_spec(),
                tasks=(
                    replace(valid_spec().tasks[0], max_attempts=0),
                )
                + valid_spec().tasks[1:],
            ),
            "FR-021",
        ),
        (
            replace(
                valid_spec(),
                tasks=(
                    replace(valid_spec().tasks[0], task_key="Invalid key"),
                )
                + valid_spec().tasks[1:],
            ),
            "FR-050",
        ),
    ),
)
def test_unpersistable_or_executable_content_is_rejected(
    bad_spec: WorkflowDraftSpec,
    rule: str,
) -> None:
    with pytest.raises(WorkflowDraftRejected) as rejected:
        service(FakeRepository()).create_draft(bad_spec)
    assert any(issue.rule == rule for issue in rejected.value.issues)
