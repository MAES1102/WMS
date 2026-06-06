import random
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.engine.events import event_bus, send_task_completed_kafka
from app.models import Task


def run_task(
    task: Task,
    db: Session,
    *,
    run_id: str,
    choreo_kafka: bool = False,
    log_event,
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

    if task.status == "DONE":
        _log("SKIPPED", f"Task {task.name} already DONE — skipping")
        return True

    task.started_at = datetime.now(UTC)
    task.finished_at = None
    task.status = "RUNNING"
    db.commit()
    _log("RUNNING", f"Task {task.name} started")

    ok_task = True
    if random.random() < 0.3:
        _log("FAILED", f"Task {task.name} failed — retrying")
        if random.random() < 0.3:
            _log("FAILED", f"Task {task.name} failed after retry")
            task.finished_at = datetime.now(UTC)
            task.status = "FAILED"
            db.commit()
            ok_task = False

    if ok_task:
        task.finished_at = datetime.now(UTC)
        task.status = "DONE"
        db.commit()
        _log("DONE", f"Task {task.name} completed")

    # BUG-02 FIX: only emit task_completed events when the task succeeded.
    # Previously events were emitted unconditionally, which caused downstream
    # choreography tasks to run even after an upstream failure.  By guarding
    # emission inside `if ok_task`, the choreography chain stops as soon as
    # any task fails — preserving correct failure-isolation semantics.
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

    return ok_task

