import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.events import create_choreo_consumer, event_bus
from app.engine.task_runner import run_task
from app.engine.transitions import (
    MAX_LOOP_ITERATIONS,
    RESULT_FAILURE,
    get_start_task,
    resolve_next_task,
    workflow_has_transitions,
)
from app.models import Task, TaskExecution, WorkflowRun


def run_choreographed_workflow(
    workflow_id: int, db: Session, *, log_event
) -> dict:
    """Run a workflow in choreography mode.

    Instead of a central controller, each task registers an EventBus handler
    that fires when the previous task emits a ``task_completed`` event.  The
    first task is started directly; all subsequent tasks are triggered
    reactively through the event chain.

    When Kafka is available (``KAFKA_BOOTSTRAP_SERVERS`` reachable) the first
    task publishes to Kafka and a consumer loop dispatches further events.
    Otherwise the in-memory EventBus is used exclusively.

    Failure isolation: ``run_task()`` only emits ``task_completed`` on success,
    so a failing task breaks the chain and downstream tasks remain PENDING.

    Args:
        workflow_id: Primary key of the Workflow to execute.  Must exist.
        db: Active SQLAlchemy session.
        log_event: Structured logging callable.

    Returns:
        Dict with keys ``workflow_id``, ``run_id``, ``mode``, and ``status``.
    """
    run_id = str(uuid.uuid4())
    run = WorkflowRun(
        id=run_id,
        workflow_id=workflow_id,
        mode="choreography",
        status="RUNNING",
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.commit()

    # Create a TaskExecution instance for every task definition in this run.
    # This separates execution state (instance) from the workflow definition.
    _tasks_all = db.scalars(
        select(Task).where(Task.workflow_id == workflow_id)
    ).all()
    task_exec_map: dict[int, TaskExecution] = {}
    for _t in _tasks_all:
        _te = TaskExecution(run_id=run_id, task_id=_t.id, status="PENDING")
        db.add(_te)
        task_exec_map[_t.id] = _te
    db.commit()

    # NEW: graph-based choreography. When the workflow defines
    # WorkflowTransition rows, task selection is delegated to the
    # TransitionResolver instead of the fixed `order` chain below.
    # Reactive, event-driven, no central loop (TaskCompletedEvent ->
    # TransitionResolver -> next Task event).
    if workflow_has_transitions(db, workflow_id):
        final_status = _run_choreography_graph(
            workflow_id, db, run_id=run_id,
            task_exec_map=task_exec_map, log_event=log_event,
        )
        run.status = final_status
        run.finished_at = datetime.now(UTC)
        db.commit()
        return {
            "workflow_id": workflow_id,
            "run_id": run_id,
            "mode": "choreography",
            "status": final_status.lower(),
        }

    # Backward compatibility: no transitions defined -> legacy order-based chain.
    tasks = sorted(
        db.scalars(select(Task).where(Task.workflow_id == workflow_id)).all(),
        key=lambda t: t.order,
    )

    event_key = f"task_completed:{run_id}"
    prev_logger = event_bus.log_event
    event_bus.log_event = log_event
    consumer = create_choreo_consumer()
    use_kafka_choreo = consumer is not None

    # каждая задача подписывается на завершение предыдущей (цепочка событий)
    for i in range(1, len(tasks)):
        # аргументы по умолчанию = фиксация i (обход late-binding в замыканиях Python)
        def handler(
            prev_task_id: int,
            cur: Task = tasks[i],
            expected: int = tasks[i - 1].id,
            session: Session = db,
            ck: bool = use_kafka_choreo,
            rid: str = run_id,
            te: TaskExecution | None = task_exec_map.get(tasks[i].id),
        ) -> None:
            if prev_task_id == expected:  # реагируем только на "своё" предыдущее событие
                log_event({
                    "workflow_id": workflow_id,
                    "run_id": rid,
                    "task_id": cur.id,
                    "task_name": cur.name,
                    "status": "EVENT_RECEIVED",
                    "message": f"EVENT RECEIVED: triggering next task after task_id={prev_task_id}",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                run_task(cur, session, run_id=rid, choreo_kafka=ck, log_event=log_event,
                         task_execution=te)  # Runtime source of truth is TaskExecution.

        event_bus.subscribe(event_key, handler)

    final_status = "COMPLETED"
    try:
        if not tasks:
            pass
        elif consumer:
            ok_first = run_task(
                tasks[0], db, run_id=run_id, choreo_kafka=True, log_event=log_event,
                task_execution=task_exec_map.get(tasks[0].id),  # Runtime source of truth is TaskExecution.
            )
            if not ok_first:
                final_status = "FAILED"
            elif not all(t.status == "DONE" for t in tasks):
                for _ in range(len(tasks) - 1):
                    batch = consumer.poll(timeout_ms=5000)
                    if not batch:
                        break
                    for _tp, msgs in batch.items():
                        for msg in msgs:
                            if msg.value:
                                tid = int(msg.value.decode("utf-8"))
                                event_bus.publish(event_key, tid)
        else:
            ok_first = run_task(
                tasks[0], db, run_id=run_id, choreo_kafka=False, log_event=log_event,
                task_execution=task_exec_map.get(tasks[0].id),  # Runtime source of truth is TaskExecution.
            )
            if not ok_first:
                final_status = "FAILED"
    finally:
        if consumer:
            consumer.close()
        event_bus.subscribers.pop(event_key, None)
        event_bus.log_event = prev_logger

    # если любая задача упала — весь run FAILED (изоляция ошибки)
    if any(t.status == "FAILED" for t in tasks):
        final_status = "FAILED"

    run.status = final_status
    run.finished_at = datetime.now(UTC)
    db.commit()

    return {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "mode": "choreography",
        "status": final_status.lower(),
    }


def _run_choreography_graph(
    workflow_id: int, db: Session, *,
    run_id: str,
    task_exec_map: dict[int, TaskExecution],
    log_event,
) -> str:
    """Reactive, transition-based choreography (no central loop).

    A single Observer handler is subscribed to the ``task_result:{run_id}``
    channel (published by ``run_task`` on every completion, success or
    failure).  Each time it fires, it asks the TransitionResolver for the
    next task and executes it directly — which in turn publishes its own
    ``task_result`` event, re-triggering this same handler.  This is the
    "TaskCompletedEvent -> TransitionResolver -> next Task event" chain
    requested by the architecture, built entirely on the existing EventBus
    Observer mechanism (no while-loop driving execution).
    """
    start = get_start_task(db, workflow_id)
    if start is None:
        return "COMPLETED"

    result_key = f"task_result:{run_id}"
    prev_logger = event_bus.log_event
    event_bus.log_event = log_event
    visited_counter: dict[int, int] = defaultdict(int)
    status_box = {"value": "COMPLETED"}

    def advance(task: Task) -> None:
        visited_counter[task.id] += 1
        if visited_counter[task.id] > MAX_LOOP_ITERATIONS:
            log_event(
                f"LOOP LIMIT: task '{task.name}' exceeded "
                f"{MAX_LOOP_ITERATIONS} iterations \u2014 marking workflow FAILED"
            )
            status_box["value"] = "FAILED"
            return
        # run_task() publishes the task_result event synchronously, which
        # invokes `handler` below before this call returns.
        run_task(task, db, run_id=run_id, choreo_kafka=False, log_event=log_event,
                 task_execution=task_exec_map.get(task.id))  # Runtime source of truth is TaskExecution.

    def handler(event) -> None:
        next_task = resolve_next_task(db, workflow_id, event.task_id, event.result)
        if next_task is None:
            # No matching transition: this branch has ended. A dangling
            # FAILURE fails the whole run; a dangling SUCCESS reached END.
            if event.result == RESULT_FAILURE:
                status_box["value"] = "FAILED"
            return
        advance(next_task)

    event_bus.subscribe(result_key, handler)
    try:
        advance(start)
    finally:
        event_bus.subscribers.pop(result_key, None)
        event_bus.log_event = prev_logger

    return status_box["value"]
