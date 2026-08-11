"""Seed "Hospital Patient Processing" — critical-system sequential workflow.

Demonstrates: a strict linear sequence where each step must succeed before
the next begins, reflecting the high-stakes nature of medical workflows.
A FAILURE branch from Verify Insurance routes to Notify Patient (patient
cannot proceed without insurance validation — early exit).

Graph shape:

    Register Patient
          | SUCCESS
    Verify Insurance
     /           \\
SUCCESS         FAILURE
   |               |
Assign Doctor  Notify Patient (insurance denied)
   | SUCCESS
Run Medical Tests
   | SUCCESS
Analyze Results
   | SUCCESS
Generate Treatment Plan
   | SUCCESS
Notify Patient

Run:
    python -m scripts.seed_hospital_patient
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Hospital Patient Processing"

TASK_NAMES = [
    "Register Patient",
    "Verify Insurance",
    "Assign Doctor",
    "Run Medical Tests",
    "Analyze Results",
    "Generate Treatment Plan",
    "Notify Patient",
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

        link("Register Patient",        "Verify Insurance",        "SUCCESS")
        # Early exit if insurance verification fails
        link("Verify Insurance",        "Assign Doctor",           "SUCCESS")
        link("Verify Insurance",        "Notify Patient",          "FAILURE")
        link("Assign Doctor",           "Run Medical Tests",       "SUCCESS")
        link("Run Medical Tests",       "Analyze Results",         "SUCCESS")
        link("Analyze Results",         "Generate Treatment Plan", "SUCCESS")
        link("Generate Treatment Plan", "Notify Patient",          "SUCCESS")
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and 7 transitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
