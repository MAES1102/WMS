import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.task_runner import run_task
from app.models import Task, WorkflowRun


def run_orchestrated_workflow(
    workflow_id: int, db: Session, *, log_event
) -> dict:
    run_id = str(uuid.uuid4())
    run = WorkflowRun(
        id=run_id,
        workflow_id=workflow_id,
        mode="orchestration",
        status="RUNNING",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()

    tasks = db.scalars(
        select(Task).where(Task.workflow_id == workflow_id)
    ).all()

    final_status = "COMPLETED"
    for task in sorted(tasks, key=lambda t: t.order):
        ok = run_task(task, db, run_id=run_id, choreo_kafka=False, log_event=log_event)
        if not ok:
            final_status = "FAILED"
            break

    run.status = final_status
    run.finished_at = datetime.utcnow()
    db.commit()

    return {"workflow_id": workflow_id, "run_id": run_id, "status": final_status.lower()}

