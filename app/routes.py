import os
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.engine.choreography import run_choreographed_workflow
from app.engine.orchestrator import run_orchestrated_workflow
from app.models import Task, User, Workflow, WorkflowRun

execution_logs = []


def log_event(entry):
    if isinstance(entry, dict):
        msg = "[{ts}] run={run} wf={wf} task={task} [{status}] {msg}".format(
            ts=(entry.get("timestamp") or "")[:19],
            run=(entry.get("run_id") or "")[:8],
            wf=entry.get("workflow_id", ""),
            task=entry.get("task_id", "?"),
            status=entry.get("status", ""),
            msg=entry.get("message", ""),
        )
    else:
        msg = str(entry)
    print(msg)
    execution_logs.append(entry)
    if len(execution_logs) > 100:
        execution_logs.pop(0)

router = APIRouter()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserCreate(BaseModel):
    email: str
    password: str


class WorkflowCreate(BaseModel):
    name: str
    user_id: int


class TaskCreate(BaseModel):
    name: str
    workflow_id: int
    order: int


@router.get("/test")
async def test() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/logs")
def get_logs() -> dict:
    return {"logs": execution_logs}


@router.post("/users")
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> dict:
    user = User(email=payload.email, password=payload.password)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")
    db.refresh(user)
    return {"id": user.id, "email": user.email}


@router.get("/users")
def list_users(db: Session = Depends(get_db)) -> list[dict]:
    users = db.scalars(select(User)).all()
    return [{"id": u.id, "email": u.email} for u in users]


@router.post("/workflows")
def create_workflow(
    payload: WorkflowCreate, db: Session = Depends(get_db)
) -> dict:
    workflow = Workflow(name=payload.name, user_id=payload.user_id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return {
        "id": workflow.id,
        "name": workflow.name,
        "user_id": workflow.user_id,
    }


@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Workflow)).all()
    return [
        {"id": w.id, "name": w.name, "user_id": w.user_id} for w in rows
    ]


@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)) -> dict:
    workflow = db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    tasks = db.scalars(
        select(Task).where(Task.workflow_id == workflow_id)
    ).all()
    for t in tasks:
        db.delete(t)

    db.delete(workflow)
    db.commit()
    return {"status": "deleted"}


@router.post("/tasks")
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> dict:
    existing = db.scalars(
        select(Task).where(
            Task.workflow_id == payload.workflow_id,
            Task.order == payload.order,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Task with this order already exists in this workflow",
        )
    task = Task(
        name=payload.name,
        workflow_id=payload.workflow_id,
        order=payload.order,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "name": task.name,
        "workflow_id": task.workflow_id,
        "order": task.order,
        "status": task.status,
    }


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Task)).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "workflow_id": t.workflow_id,
            "order": t.order,
            "status": t.status,
            "started_at": t.started_at,
            "finished_at": t.finished_at,
            "duration_seconds": (
                (t.finished_at - t.started_at).total_seconds()
                if (t.started_at and t.finished_at)
                else None
            ),
        }
        for t in rows
    ]


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "name": task.name,
        "workflow_id": task.workflow_id,
        "order": task.order,
        "status": task.status,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "duration_seconds": (
            (task.finished_at - task.started_at).total_seconds()
            if (task.started_at and task.finished_at)
            else None
        ),
    }


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workflow_id = task.workflow_id
    db.delete(task)
    db.commit()

    tasks = db.scalars(
        select(Task)
        .where(Task.workflow_id == workflow_id)
        .order_by(Task.order)
    ).all()
    for index, t in enumerate(tasks, start=1):
        t.order = index
    db.commit()
    return {"status": "deleted"}


@router.get("/workflows/{workflow_id}/status")
def workflow_status(workflow_id: int, db: Session = Depends(get_db)) -> dict:
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    tasks = (
        db.scalars(select(Task).where(Task.workflow_id == workflow_id)).all()
        or []
    )
    tasks_sorted = sorted(tasks, key=lambda t: t.order)

    done_tasks = sum(1 for t in tasks_sorted if t.status == "DONE")
    running_tasks = sum(1 for t in tasks_sorted if t.status == "RUNNING")
    pending_tasks = sum(1 for t in tasks_sorted if t.status == "PENDING")

    return {
        "workflow": {
            "id": workflow.id,
            "name": workflow.name,
            "user_id": workflow.user_id,
        },
        "summary": {
            "total_tasks": len(tasks_sorted),
            "done_tasks": done_tasks,
            "pending_tasks": pending_tasks,
            "running_tasks": running_tasks,
        },
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "order": t.order,
                "status": t.status,
                "started_at": t.started_at,
                "finished_at": t.finished_at,
                "duration_seconds": (
                    (t.finished_at - t.started_at).total_seconds()
                    if (t.started_at and t.finished_at)
                    else None
                ),
            }
            for t in tasks_sorted
        ],
    }


@router.get("/workflow_runs/{workflow_id}")
def list_workflow_runs(
    workflow_id: int, db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.scalars(
        select(WorkflowRun).where(WorkflowRun.workflow_id == workflow_id)
    ).all()
    return [
        {
            "id": r.id,
            "workflow_id": r.workflow_id,
            "mode": r.mode,
            "status": r.status,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
        }
        for r in rows
    ]


@router.post("/execute/{workflow_id}")
def execute_workflow(
    workflow_id: int, db: Session = Depends(get_db)
) -> dict:
    if not db.get(Workflow, workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    log_event("=== ORCHESTRATION MODE ===")
    return run_orchestrated_workflow(workflow_id, db, log_event=log_event)


@router.post("/execute_choreo/{workflow_id}")
def execute_workflow_choreo(
    workflow_id: int, db: Session = Depends(get_db)
) -> dict:
    if not db.get(Workflow, workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    log_event("=== CHOREOGRAPHY MODE ===")
    return run_choreographed_workflow(workflow_id, db, log_event=log_event)


@router.get("/ui")
def workflow_ui():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
