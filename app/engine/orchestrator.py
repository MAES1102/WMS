import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.task_runner import run_task
from app.engine.transitions import (
    MAX_LOOP_ITERATIONS,
    RESULT_FAILURE,
    RESULT_SUCCESS,
    get_start_task,
    resolve_next_task,
    workflow_has_transitions,
)
from app.models import Task, TaskExecution, WorkflowRun


def run_orchestrated_workflow(
    workflow_id: int, db: Session, *, log_event
) -> dict:
    """Run a workflow in orchestration mode.

    The central controller now owns a small workflow *state machine*:
    it picks the current node, executes it, evaluates the SUCCESS/FAILURE
    result, and follows the matching ``WorkflowTransition`` edge to the next
    node — supporting branching, decision gateways, and retry loops.

    Backward compatibility: workflows that define no ``WorkflowTransition``
    rows fall back to the legacy behaviour of executing tasks strictly by
    ``order``, fail-fast on the first error.

    Args:
        workflow_id: Primary key of the Workflow to execute.  Must exist.
        db: Active SQLAlchemy session.
        log_event: Structured logging callable.

    Returns:
        Dict with keys ``workflow_id``, ``run_id``, and ``status``.
    """
    run_id = str(uuid.uuid4())
    run = WorkflowRun(
        id=run_id,
        workflow_id=workflow_id,
        mode="orchestration",
        status="RUNNING",
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.commit()

    # Create a TaskExecution instance for every task definition in this run.
    # This separates execution state (instance) from the workflow definition.
    tasks_all = db.scalars(
        select(Task).where(Task.workflow_id == workflow_id)
    ).all()
    task_exec_map: dict[int, TaskExecution] = {}
    for t in tasks_all:
        te = TaskExecution(run_id=run_id, task_id=t.id, status="PENDING")
        db.add(te)
        task_exec_map[t.id] = te
    db.commit()

    if workflow_has_transitions(db, workflow_id):
        final_status = _run_graph(
            workflow_id, db, run_id=run_id,
            task_exec_map=task_exec_map, log_event=log_event,
        )
    else:
        final_status = _run_sequential(
            workflow_id, db, run_id=run_id,
            task_exec_map=task_exec_map, log_event=log_event,
        )

    run.status = final_status
    run.finished_at = datetime.now(UTC)
    db.commit()

    return {"workflow_id": workflow_id, "run_id": run_id, "status": final_status.lower()}


def _run_sequential(
    workflow_id: int, db: Session, *,
    run_id: str,
    task_exec_map: dict[int, TaskExecution],
    log_event,
) -> str:
    """Legacy behaviour: iterate tasks in ``order``, fail-fast."""
    tasks = db.scalars(
        select(Task).where(Task.workflow_id == workflow_id)
    ).all()

    # оркестрация: центральный цикл идёт по задачам в порядке order
    for task in sorted(tasks, key=lambda t: t.order):
        ok = run_task(
            task, db,
            run_id=run_id,
            choreo_kafka=False,
            log_event=log_event,
            task_execution=task_exec_map.get(task.id),
        )
        if not ok:
            # fail-fast: первая же ошибка останавливает весь процесс
            return "FAILED"
    return "COMPLETED"


def _run_graph(
    workflow_id: int, db: Session, *,
    run_id: str,
    task_exec_map: dict[int, TaskExecution],
    log_event,
) -> str:
    """Graph traversal state machine:

    current = start_task
    while current:
        execute current task
        result = SUCCESS or FAILURE
        transition = find transition where from_task=current, condition=result
        current = transition.to_task
    """
    current = get_start_task(db, workflow_id)
    if current is None:
        return "COMPLETED"

    visited_counter: dict[int, int] = defaultdict(int)

    while current is not None:
        visited_counter[current.id] += 1
        if visited_counter[current.id] > MAX_LOOP_ITERATIONS:
            log_event(
                f"LOOP LIMIT: task '{current.name}' exceeded "
                f"{MAX_LOOP_ITERATIONS} iterations — marking workflow FAILED"
            )
            return "FAILED"

        ok = run_task(
            current, db,
            run_id=run_id,
            choreo_kafka=False,
            log_event=log_event,
            task_execution=task_exec_map.get(current.id),
        )
        result = RESULT_SUCCESS if ok else RESULT_FAILURE

        next_task = resolve_next_task(db, workflow_id, current.id, result)
        if next_task is None:
            # No outgoing edge for this outcome: end of this branch.
            # A FAILURE with nowhere to go fails the whole run; a SUCCESS
            # with nowhere to go means the branch reached the implicit END.
            return "FAILED" if result == RESULT_FAILURE else "COMPLETED"
        current = next_task

    return "COMPLETED"

