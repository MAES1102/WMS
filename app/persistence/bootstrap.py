"""Schema bootstrap and reference-workflow initialization."""

from datetime import UTC, datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.persistence.database import Base
from app.persistence import models  # noqa: F401
from app.persistence.models import (
    DraftTask,
    DraftTransition,
    RevisionTask,
    RevisionTransition,
    WorkflowDraft,
    WorkflowRevision,
)


WORKFLOW_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name.startswith("purchase_request_") or table.name == "purchase_requests"
)


def create_purchase_request_schema(engine: Engine) -> None:
    """Create the purchase_request application schema."""
    Base.metadata.create_all(engine, tables=WORKFLOW_TABLES)


def ensure_reference_workflow(session: Session) -> int:
    """Create the bounded purchase_request workflow once and return its revision id."""
    existing = session.scalars(
        select(WorkflowRevision).order_by(WorkflowRevision.id)
    ).first()
    if existing is not None:
        if _ensure_editable_snapshot(session, existing):
            session.commit()
        return existing.id

    now = datetime.now(UTC)
    draft = WorkflowDraft(
        name="Purchase Request Approval",
        created_at=now,
        updated_at=now,
    )
    session.add(draft)
    session.flush()
    revision = WorkflowRevision(
        draft_id=draft.id,
        revision_number=1,
        name=draft.name,
        activated_at=now,
    )
    session.add(revision)
    session.flush()

    validate = RevisionTask(
        revision_id=revision.id,
        task_key="validate",
        name="Validate Purchase Request",
        task_type="REQUEST_VALIDATION",
        is_start=True,
        max_attempts=1,
    )
    review = RevisionTask(
        revision_id=revision.id,
        task_key="review",
        name="Human Approval",
        task_type="HUMAN_APPROVAL",
        is_start=False,
        max_attempts=None,
    )
    authorization = RevisionTask(
        revision_id=revision.id,
        task_key="authorize",
        name="Create Purchase Authorization",
        task_type="PURCHASE_AUTHORIZATION",
        is_start=False,
        max_attempts=2,
    )
    notify = RevisionTask(
        revision_id=revision.id,
        task_key="notify",
        name="Record Notification",
        task_type="CREATE_NOTIFICATION",
        is_start=False,
        max_attempts=2,
    )
    session.add_all((validate, review, authorization, notify))
    session.flush()
    session.add_all(
        RevisionTransition(
            revision_id=revision.id,
            from_task_id=source.id,
            to_task_id=target.id,
            condition=condition,
        )
        for source, target, condition in (
            (validate, review, "SUCCESS"),
            (validate, notify, "FAILURE"),
            (review, authorization, "SUCCESS"),
            (review, notify, "FAILURE"),
            (authorization, notify, "SUCCESS"),
            (authorization, notify, "FAILURE"),
        )
    )
    session.flush()
    _ensure_editable_snapshot(session, revision)
    session.commit()
    return revision.id


def _ensure_editable_snapshot(
    session: Session,
    revision: WorkflowRevision,
) -> bool:
    """Backfill an editable draft from an existing immutable reference revision."""
    existing_task = session.scalars(
        select(DraftTask).where(DraftTask.draft_id == revision.draft_id)
    ).first()
    if existing_task is not None:
        return False

    revision_tasks = session.scalars(
        select(RevisionTask)
        .where(RevisionTask.revision_id == revision.id)
        .order_by(RevisionTask.id)
    ).all()
    draft_by_revision_id: dict[int, DraftTask] = {}
    for task in revision_tasks:
        copied = DraftTask(
            draft_id=revision.draft_id,
            task_key=task.task_key,
            name=task.name,
            task_type=task.task_type,
            is_start=task.is_start,
            max_attempts=task.max_attempts,
        )
        session.add(copied)
        session.flush()
        draft_by_revision_id[task.id] = copied

    revision_transitions = session.scalars(
        select(RevisionTransition)
        .where(RevisionTransition.revision_id == revision.id)
        .order_by(RevisionTransition.id)
    ).all()
    session.add_all(
        DraftTransition(
            draft_id=revision.draft_id,
            from_task_id=draft_by_revision_id[item.from_task_id].id,
            to_task_id=draft_by_revision_id[item.to_task_id].id,
            condition=item.condition,
        )
        for item in revision_transitions
    )
    return bool(revision_tasks)
