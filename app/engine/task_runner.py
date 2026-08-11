import random
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.engine.events import TaskCompletedEvent, event_bus, send_task_completed_kafka
from app.models import Task, TaskExecution


def run_task(
    task: Task,
    db: Session,
    *,
    run_id: str,
    choreo_kafka: bool = False,
    log_event,
    task_execution: TaskExecution | None = None,
) -> bool:
    """Execute a single task and persist its status to the database.

    Simulates a probabilistic failure (9% hard-fail, 21% transient logged as
    retrying then succeeds) to demonstrate retry semantics.  On success a
    ``task_completed`` event is published to the EventBus and/or Kafka so that
    choreography handlers can trigger the next task.  On failure **no event is
    emitted** — this is intentional: it prevents downstream choreography tasks
    from running after an upstream failure (BUG-02 fix).

    Args:
        task: ORM Task object (must belong to the db session).
        db: Active SQLAlchemy session.
        run_id: UUID string of the current WorkflowRun.
        choreo_kafka: When True, attempt Kafka publishing first and fall back to
            the in-memory EventBus.
        log_event: Callable that accepts a structured log dict.

    Returns:
        ``True`` if the task completed successfully, ``False`` if it failed.
    """
    def _log(status: str, message: str) -> None:
        log_event({
            "workflow_id": task.workflow_id,
            "run_id": run_id,
            "task_id": task.id,
            "task_name": task.name,
            "status": status,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    # идемпотентность: prefer TaskExecution.status when available (instance layer),
    # fall back to Task.status for legacy callers without task_execution.
    effective_status = task_execution.status if task_execution is not None else task.status
    if effective_status == "DONE":
        _log("SKIPPED", f"Task {task.name} already DONE — skipping")
        return True

    task.started_at = datetime.now(UTC)  # legacy UI compatibility
    task.finished_at = None               # legacy UI compatibility
    task.status = "RUNNING"               # legacy UI compatibility
    if task_execution is not None:
        task_execution.started_at = datetime.now(UTC)
        task_execution.finished_at = None
        task_execution.status = "RUNNING"
    db.commit()
    _log("RUNNING", f"Task {task.name} started")

    ok_task = True
    # имитация сбоя + retry: демонстрация отказоустойчивости
    if random.random() < 0.3:
        _log("FAILED", f"Task {task.name} failed — retrying")
        if random.random() < 0.3:  # повтор не помог → жёсткий отказ
            _log("FAILED", f"Task {task.name} failed after retry")
            task.finished_at = datetime.now(UTC)  # legacy UI compatibility
            task.status = "FAILED"                # legacy UI compatibility
            if task_execution is not None:
                task_execution.finished_at = datetime.now(UTC)
                task_execution.status = "FAILED"
            db.commit()
            ok_task = False

    if ok_task:
        task.finished_at = datetime.now(UTC)  # legacy UI compatibility
        task.status = "DONE"                  # legacy UI compatibility
        if task_execution is not None:
            task_execution.finished_at = datetime.now(UTC)
            task_execution.status = "DONE"
        db.commit()
        _log("DONE", f"Task {task.name} completed")

    # BUG-02 FIX: событие task_completed только при успехе → сбой рвёт цепочку хореографии
    # BUG-02 FIX: only emit task_completed events when the task succeeded.
    # Previously events were emitted unconditionally, which caused downstream
    # choreography tasks to run even after an upstream failure.  By guarding
    # emission inside `if ok_task`, the choreography chain stops as soon as
    # any task fails — preserving correct failure-isolation semantics.
    # This legacy channel is kept exactly as-is so the old order-based
    # choreography chain (no WorkflowTransition rows) keeps working.
    if ok_task:
        event_key = f"task_completed:{run_id}"
        if choreo_kafka or bool(event_bus.subscribers.get(event_key)):
            _log("TASK_COMPLETED", f"EVENT: task_completed \u2192 {task.name}")
        if choreo_kafka:
            if not send_task_completed_kafka(task.id):
                event_bus.publish(event_key, task.id)
        else:
            if event_bus.subscribers.get(event_key):
                event_bus.publish(event_key, task.id)
    else:
        # Log the failure without triggering downstream tasks.
        _log("TASK_FAILED", f"EVENT: task_failed \u2192 {task.name} (downstream tasks will not run)")

    # NEW: graph-based "task_result" event, published on both success AND
    # failure (unlike the legacy channel above) so that FAILURE transitions
    # (e.g. retry/cancel branches) can react to a failed task.  Only fires
    # if a listener is registered, i.e. only for the new transition-based
    # choreography — it never touches the legacy chain.
    result_key = f"task_result:{run_id}"
    if event_bus.subscribers.get(result_key):
        event_bus.publish(
            result_key,
            TaskCompletedEvent(
                task_id=task.id,
                workflow_id=task.workflow_id,
                result="SUCCESS" if ok_task else "FAILURE",
                output=None,
            ),
        )

    return ok_task

