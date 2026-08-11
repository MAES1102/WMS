"""Workflow graph resolution: turns Task + WorkflowTransition rows into a
traversable graph.

This module is the heart of the BPMN-like upgrade: instead of a flat,
ordered task list, a workflow is a directed graph where each edge
(``WorkflowTransition``) is only followed when the source task finished with
a matching ``condition`` (``SUCCESS`` / ``FAILURE`` / ``ALWAYS``).

Both the orchestrator (central loop) and the choreography engine (reactive
event chain) share this resolver so branching/looping semantics are
identical in both execution modes.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task, WorkflowTransition

# Task execution outcomes that drive transition selection.
RESULT_SUCCESS = "SUCCESS"
RESULT_FAILURE = "FAILURE"
CONDITION_ALWAYS = "ALWAYS"

# Safety valve for retry loops (e.g. ChargeCard -> RetryPayment -> ChargeCard).
# Without this a misconfigured graph could loop forever.
MAX_LOOP_ITERATIONS = 10


def workflow_has_transitions(db: Session, workflow_id: int) -> bool:
    """True if *workflow_id* has at least one WorkflowTransition defined.

    Used by the orchestrator/choreography engines to decide whether to run
    the new graph-traversal engine or fall back to the legacy ``order``
    based sequential executor (backward compatibility).
    """
    row = db.scalars(
        select(WorkflowTransition.id).where(
            WorkflowTransition.workflow_id == workflow_id
        )
    ).first()
    return row is not None


def get_start_task(db: Session, workflow_id: int) -> Task | None:
    """Pick the entry point ("START") node of the workflow graph.

    A task is a valid start node if no transition points *to* it (no
    incoming edges).  Among candidates, the one with the smallest
    ``order`` wins so demo/seed data with an implicit order is deterministic.
    Falls back to the task with smallest ``order`` if every task has an
    incoming edge (e.g. a purely cyclic graph).
    """
    tasks = db.scalars(
        select(Task).where(Task.workflow_id == workflow_id)
    ).all()
    if not tasks:
        return None

    targets = {
        t.to_task_id
        for t in db.scalars(
            select(WorkflowTransition).where(
                WorkflowTransition.workflow_id == workflow_id
            )
        ).all()
    }
    candidates = [t for t in tasks if t.id not in targets]
    pool = candidates or list(tasks)
    return min(pool, key=lambda t: t.order)


def resolve_next_task(
    db: Session, workflow_id: int, from_task_id: int, result: str
) -> Task | None:
    """Find the next Task to execute after *from_task_id* finished with *result*.

    Selection rules (BPMN decision-gateway semantics):
    1. Prefer an edge whose ``condition`` matches *result* exactly.
    2. Otherwise fall back to an ``ALWAYS`` edge.
    3. Among multiple matching edges, the lowest ``priority`` value wins.
    4. If no edge matches, the graph ends on this branch (returns ``None``).
    """
    transitions = db.scalars(
        select(WorkflowTransition).where(
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.from_task_id == from_task_id,
        )
    ).all()
    if not transitions:
        return None

    matching = [t for t in transitions if t.condition == result]
    if not matching:
        matching = [t for t in transitions if t.condition == CONDITION_ALWAYS]
    if not matching:
        return None

    best = min(matching, key=lambda t: t.priority)
    return db.get(Task, best.to_task_id)
