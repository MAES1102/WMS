"""Seed "Failure & Retry Demonstration" — explicitly shows retry and error handling.

Demonstrates: the engine's built-in retry mechanism and the FAILURE branch
routing. "Unstable External API Call" has a high chance of triggering the
engine's automatic retry (task_runner uses random() < 0.3 for transient
failure then 0.3 again for hard failure). The FAILURE transition loops back
to retry the call from the graph level (graph-level retry on top of the
engine's internal retry).

Graph shape:

    Stable Task
          | SUCCESS
    Unstable External API Call  <──────────────┐
          | SUCCESS                             │
    Final Processing Step        FAILURE ───────┘
                                 (graph-level retry loop: max 10 per engine)

Run:
    python -m scripts.seed_failure_demo
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Failure & Retry Demonstration"

TASK_NAMES = [
    "Stable Task",
    "Unstable External API Call",
    "Final Processing Step",
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(email=DEMO_EMAIL, password="demo")
            db.add(user)
            db.commit()
            db.refresh(user)

        existing = (
            db.query(Workflow)
            .filter(Workflow.name == DEMO_WORKFLOW_NAME, Workflow.user_id == user.id)
            .first()
        )
        if existing is not None:
            print(f"'{DEMO_WORKFLOW_NAME}' already exists (id={existing.id}) — skipping.")
            return

        workflow = Workflow(name=DEMO_WORKFLOW_NAME, user_id=user.id)
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        tasks: dict[str, Task] = {}
        for order, name in enumerate(TASK_NAMES, start=1):
            task = Task(name=name, workflow_id=workflow.id, order=order)
            db.add(task)
            db.commit()
            db.refresh(task)
            tasks[name] = task

        def link(from_name: str, to_name: str, condition: str) -> None:
            db.add(WorkflowTransition(
                workflow_id=workflow.id,
                from_task_id=tasks[from_name].id,
                to_task_id=tasks[to_name].id,
                condition=condition,
            ))

        link("Stable Task",                "Unstable External API Call", "SUCCESS")
        # On success: continue to final step
        link("Unstable External API Call", "Final Processing Step",      "SUCCESS")
        # On failure: loop back (graph-level retry, capped by MAX_LOOP_ITERATIONS=10)
        link("Unstable External API Call", "Unstable External API Call", "FAILURE")
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and 3 transitions (including self-retry loop).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
