"""Seed "AI Data Processing Pipeline" — data engineering workflow with retry loop.

Demonstrates: a model-training loop where failed accuracy evaluation routes
back to Train Model (retry from an earlier node) — a realistic ML pipeline
that retrains when the model doesn't meet the accuracy threshold.

Graph shape:

    Collect Raw Data
          | SUCCESS
    Validate Dataset
          | SUCCESS
    Clean Data
          | SUCCESS
    Train Model  <─────────────────────┐
          | SUCCESS                     │
    Evaluate Accuracy                   │
     /           \\                     │
SUCCESS         FAILURE (retrain loop) ─┘
   |
Deploy Model
   | SUCCESS
Monitor Performance

Run:
    python -m scripts.seed_ai_pipeline
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "AI Data Processing Pipeline"

TASK_NAMES = [
    "Collect Raw Data",
    "Validate Dataset",
    "Clean Data",
    "Train Model",
    "Evaluate Accuracy",
    "Deploy Model",
    "Monitor Performance",
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

        def link(from_name: str, to_name: str, condition: str, priority: int = 0) -> None:
            db.add(WorkflowTransition(
                workflow_id=workflow.id,
                from_task_id=tasks[from_name].id,
                to_task_id=tasks[to_name].id,
                condition=condition,
                priority=priority,
            ))

        link("Collect Raw Data",   "Validate Dataset",    "SUCCESS")
        link("Validate Dataset",   "Clean Data",          "SUCCESS")
        link("Clean Data",         "Train Model",         "SUCCESS")
        link("Train Model",        "Evaluate Accuracy",   "SUCCESS")
        # Accuracy gate: success → deploy, failure → retrain loop
        link("Evaluate Accuracy",  "Deploy Model",        "SUCCESS")
        link("Evaluate Accuracy",  "Train Model",         "FAILURE")   # retrain loop
        link("Deploy Model",       "Monitor Performance", "SUCCESS")
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and 7 transitions (including retrain loop).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
