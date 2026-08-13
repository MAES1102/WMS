from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.application.constructor import (
    DraftTaskSpec,
    DraftTransitionSpec,
    WorkflowActivationRejected,
    WorkflowConstructorConflict,
    WorkflowConstructorService,
    WorkflowDraftSpec,
)
from app.persistence.constructor import SqlAlchemyWorkflowConstructorRepository
from app.persistence.models import WorkflowRevision


def valid_spec(name: str = "Invoice approval") -> WorkflowDraftSpec:
    return WorkflowDraftSpec(
        name,
        (
            DraftTaskSpec("validate", "Validate", "DOCUMENT_VALIDATION", True, 1),
            DraftTaskSpec("review", "Review", "HUMAN_APPROVAL", False, None),
            DraftTaskSpec("archive", "Archive", "ARCHIVE_DOCUMENT", False, 2),
            DraftTaskSpec("notify", "Notify", "CREATE_NOTIFICATION", False, 1),
        ),
        (
            DraftTransitionSpec("validate", "review", "SUCCESS"),
            DraftTransitionSpec("validate", "notify", "FAILURE"),
            DraftTransitionSpec("review", "archive", "SUCCESS"),
            DraftTransitionSpec("review", "notify", "FAILURE"),
            DraftTransitionSpec("archive", "notify", "SUCCESS"),
            DraftTransitionSpec("archive", "notify", "FAILURE"),
        ),
    )


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 8, 13, 16, 0, tzinfo=UTC)

    def __call__(self):
        value = self.now
        self.now += timedelta(seconds=1)
        return value


def test_crud_activation_and_revision_history_are_isolated(db) -> None:
    service = WorkflowConstructorService(
        SqlAlchemyWorkflowConstructorRepository(db),
        Clock(),
    )
    created = service.create_draft(valid_spec())
    revision_one = service.activate_draft(created.id)
    changed_spec = replace(
        valid_spec("Invoice approval revised"),
        tasks=(
            replace(valid_spec().tasks[0], name="Validate PDF and metadata"),
        )
        + valid_spec().tasks[1:],
    )
    updated = service.replace_draft(created.id, changed_spec)
    revision_two = service.activate_draft(created.id)

    assert updated.latest_revision_number == 1
    assert revision_one.revision_number == 1
    assert revision_two.revision_number == 2
    assert service.get_revision(revision_one.id).spec.tasks[0].name == "Validate"
    assert service.get_revision(revision_two.id).spec.tasks[0].name == (
        "Validate PDF and metadata"
    )
    assert len(service.list_drafts()) == 1

    with pytest.raises(WorkflowConstructorConflict, match="revision history"):
        service.delete_draft(created.id)


def test_unactivated_draft_can_be_deleted_without_affecting_another(db) -> None:
    service = WorkflowConstructorService(
        SqlAlchemyWorkflowConstructorRepository(db),
        Clock(),
    )
    first = service.create_draft(valid_spec("First"))
    second = service.create_draft(valid_spec("Second"))

    service.delete_draft(first.id)

    assert [draft.id for draft in service.list_drafts()] == [second.id]


def test_invalid_draft_creates_no_revision(db) -> None:
    service = WorkflowConstructorService(
        SqlAlchemyWorkflowConstructorRepository(db),
        Clock(),
    )
    invalid = replace(
        valid_spec(),
        tasks=tuple(replace(task, is_start=False) for task in valid_spec().tasks),
    )
    draft = service.create_draft(invalid)

    with pytest.raises(WorkflowActivationRejected):
        service.activate_draft(draft.id)

    count = db.scalar(select(func.count()).select_from(WorkflowRevision))
    assert count == 0
