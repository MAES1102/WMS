import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.events import create_choreo_consumer, event_bus
from app.engine.task_runner import run_task
from app.models import Task, WorkflowRun


def run_choreographed_workflow(
    workflow_id: int, db: Session, *, log_event
) -> dict:
    run_id = str(uuid.uuid4())
    run = WorkflowRun(
        id=run_id,
        workflow_id=workflow_id,
        mode="choreography",
        status="RUNNING",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()

    tasks = sorted(
        db.scalars(select(Task).where(Task.workflow_id == workflow_id)).all(),
        key=lambda t: t.order,
    )

    event_key = f"task_completed:{run_id}"
    prev_logger = event_bus.log_event
    event_bus.log_event = log_event
    consumer = create_choreo_consumer()
    use_kafka_choreo = consumer is not None

    for i in range(1, len(tasks)):
        def handler(
            prev_task_id: int,
            cur: Task = tasks[i],
            expected: int = tasks[i - 1].id,
            session: Session = db,
            ck: bool = use_kafka_choreo,
            rid: str = run_id,
        ) -> None:
            if prev_task_id == expected:
                log_event({
                    "workflow_id": workflow_id,
                    "run_id": rid,
                    "task_id": cur.id,
                    "task_name": cur.name,
                    "status": "EVENT_RECEIVED",
                    "message": f"EVENT RECEIVED: triggering next task after task_id={prev_task_id}",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                run_task(cur, session, run_id=rid, choreo_kafka=ck, log_event=log_event)

        event_bus.subscribe(event_key, handler)

    final_status = "COMPLETED"
    try:
        if not tasks:
            pass
        elif consumer:
            ok_first = run_task(
                tasks[0], db, run_id=run_id, choreo_kafka=True, log_event=log_event
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
                tasks[0], db, run_id=run_id, choreo_kafka=False, log_event=log_event
            )
            if not ok_first:
                final_status = "FAILED"
    finally:
        if consumer:
            consumer.close()
        event_bus.subscribers.pop(event_key, None)
        event_bus.log_event = prev_logger

    if any(t.status == "FAILED" for t in tasks):
        final_status = "FAILED"

    run.status = final_status
    run.finished_at = datetime.utcnow()
    db.commit()

    return {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "mode": "choreography",
        "status": final_status.lower(),
    }

