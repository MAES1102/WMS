"""Helpers shared by the approval and automatic-step SQLAlchemy adapters."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.application.errors import StateVersionConflict
from app.domain.types import TaskDefinition, TaskType, TransitionCondition, TransitionDefinition
from app.persistence.models import (
    ExecutionCursor,
    PurchaseRequestTraceEntry,
    RevisionTask,
    RevisionTransition,
)


def apply_version_gated_cursor_update(
    session: Session,
    *,
    run_id: str,
    expected_version: int,
    required_phase: str,
    required_task_id: int,
    values: dict,
    conflict_message: str,
) -> None:
    """Advance the execution cursor only if it still matches the expected version/phase/task."""
    result = session.execute(
        update(ExecutionCursor)
        .where(
            ExecutionCursor.run_id == run_id,
            ExecutionCursor.state_version == expected_version,
            ExecutionCursor.phase == required_phase,
            ExecutionCursor.current_task_id == required_task_id,
        )
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise StateVersionConflict(conflict_message)


def query_transitions(
    session: Session,
    revision_id: int,
    task_id: int,
) -> tuple[TransitionDefinition, ...]:
    rows = session.scalars(
        select(RevisionTransition)
        .where(
            RevisionTransition.revision_id == revision_id,
            RevisionTransition.from_task_id == task_id,
        )
        .order_by(RevisionTransition.id)
    ).all()
    return tuple(
        TransitionDefinition(
            id=row.id,
            from_task_id=row.from_task_id,
            to_task_id=row.to_task_id,
            condition=TransitionCondition(row.condition),
        )
        for row in rows
    )


def build_task_definition(task: RevisionTask) -> TaskDefinition:
    return TaskDefinition(
        id=task.id,
        name=task.name,
        task_type=TaskType(task.task_type),
        is_start=task.is_start,
        max_attempts=task.max_attempts,
    )


def next_trace_position(session: Session, run_id: str) -> int:
    return int(
        session.scalar(
            select(func.max(PurchaseRequestTraceEntry.position)).where(
                PurchaseRequestTraceEntry.run_id == run_id
            )
        )
        or 0
    )


def format_trace_detail(detail: str | None, transition_id: int | None) -> str | None:
    if transition_id is None:
        return detail
    transition_detail = f"transition_id={transition_id}"
    return f"{detail}; {transition_detail}" if detail else transition_detail
