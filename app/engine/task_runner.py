import random
from datetime import datetime

from sqlalchemy.orm import Session

from app.engine.events import event_bus, send_task_completed_kafka
from app.models import Task


def run_task(
    task: Task, db: Session, *, run_id: str, choreo_kafka: bool = False, log_event
) -> bool:
    def _log(status: str, message: str) -> None:
        log_event({
            "workflow_id": task.workflow_id,
            "run_id": run_id,
            "task_id": task.id,
            "task_name": task.name,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

    if task.status == "DONE":
        _log("SKIPPED", f"Task {task.name} already DONE — skipping")
        return True

    task.started_at = datetime.utcnow()
    task.finished_at = None
    task.status = "RUNNING"
    db.commit()
    _log("RUNNING", f"Task {task.name} started")

    ok_task = True
    if random.random() < 0.3:
        _log("FAILED", f"Task {task.name} failed — retrying")
        if random.random() < 0.3:
            _log("FAILED", f"Task {task.name} failed after retry")
            task.finished_at = datetime.utcnow()
            task.status = "FAILED"
            db.commit()
            ok_task = False

    if ok_task:
        task.finished_at = datetime.utcnow()
        task.status = "DONE"
        db.commit()
        _log("DONE", f"Task {task.name} completed")

    event_key = f"task_completed:{run_id}"
    should_emit = choreo_kafka or bool(event_bus.subscribers.get(event_key))
    if should_emit:
        label = "task_failed" if task.status == "FAILED" else "task_completed"
        _log(label.upper(), f"EVENT: {label} \u2192 {task.name}")

    if choreo_kafka:
        if not send_task_completed_kafka(task.id):
            event_bus.publish(event_key, task.id)
    else:
        if event_bus.subscribers.get(event_key):
            event_bus.publish(event_key, task.id)

    return ok_task

