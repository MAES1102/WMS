"""Tests for WorkflowRun + TaskExecution model layer.

Validates that workflow definition and execution state are properly separated:
  - One WorkflowDefinition (Workflow + Tasks) can spawn multiple WorkflowRun instances.
  - Each WorkflowRun owns independent TaskExecution records.
  - Mutating a TaskExecution in one run does not affect another run or the
    shared Task definition object.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  ensure all models are registered before create_all
from app.db import Base
from app.models import Task, TaskExecution, User, Workflow, WorkflowRun


@pytest.fixture()
def db():
    """Fresh in-memory SQLite session scoped to one test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ── helpers ──────────────────────────────────────────────────────────────────

def _seed_workflow(db):
    """Create a user + workflow + two task definitions. Returns (workflow, task_a, task_b)."""
    user = User(email="runs@test.com", password="pw")
    db.add(user)
    db.flush()

    wf = Workflow(name="Run Test WF", user_id=user.id)
    db.add(wf)
    db.flush()

    task_a = Task(name="Step A", workflow_id=wf.id, order=1)
    task_b = Task(name="Step B", workflow_id=wf.id, order=2)
    db.add_all([task_a, task_b])
    db.flush()

    return wf, task_a, task_b


# ── Test 1 ────────────────────────────────────────────────────────────────────

def test_workflow_can_have_multiple_runs(db):
    """One workflow definition can spawn multiple independent WorkflowRun instances,
    each with their own set of TaskExecution records."""
    wf, task_a, task_b = _seed_workflow(db)
    now = datetime.now(timezone.utc)

    run1 = WorkflowRun(id="run-1", workflow_id=wf.id, mode="orchestration",
                       status="RUNNING", started_at=now)
    run2 = WorkflowRun(id="run-2", workflow_id=wf.id, mode="choreography",
                       status="RUNNING", started_at=now)
    db.add_all([run1, run2])
    db.flush()

    # Each run gets its own TaskExecution rows
    for run_id in ("run-1", "run-2"):
        db.add_all([
            TaskExecution(run_id=run_id, task_id=task_a.id, status="PENDING"),
            TaskExecution(run_id=run_id, task_id=task_b.id, status="PENDING"),
        ])
    db.commit()

    runs = db.scalars(select(WorkflowRun).where(WorkflowRun.workflow_id == wf.id)).all()
    assert len(runs) == 2, "Same workflow should have exactly two runs"

    for run_id in ("run-1", "run-2"):
        execs = db.scalars(
            select(TaskExecution).where(TaskExecution.run_id == run_id)
        ).all()
        assert len(execs) == 2, f"{run_id} should have TaskExecution for each task"


# ── Test 2 ────────────────────────────────────────────────────────────────────

def test_task_executions_are_isolated_across_runs(db):
    """Advancing a TaskExecution to DONE in Run A must not affect Run B's
    TaskExecution or the shared Task definition object."""
    wf, task_a, _ = _seed_workflow(db)
    now = datetime.now(timezone.utc)

    run_a = WorkflowRun(id="run-a", workflow_id=wf.id, mode="orchestration",
                        status="RUNNING", started_at=now)
    run_b = WorkflowRun(id="run-b", workflow_id=wf.id, mode="orchestration",
                        status="RUNNING", started_at=now)
    db.add_all([run_a, run_b])
    db.flush()

    exec_a = TaskExecution(run_id="run-a", task_id=task_a.id, status="PENDING")
    exec_b = TaskExecution(run_id="run-b", task_id=task_a.id, status="PENDING")
    db.add_all([exec_a, exec_b])
    db.commit()

    # Advance only Run A's execution to DONE
    exec_a.status = "DONE"
    exec_a.started_at = now
    exec_a.finished_at = datetime.now(timezone.utc)
    db.commit()

    # Re-fetch all three objects from the DB
    a = db.get(TaskExecution, exec_a.id)
    b = db.get(TaskExecution, exec_b.id)
    definition = db.get(Task, task_a.id)

    assert a.status == "DONE",    "Run A's TaskExecution should be DONE"
    assert b.status == "PENDING", "Run B's TaskExecution must remain PENDING"
    assert definition.status == "PENDING", "Shared Task definition must be unchanged"
