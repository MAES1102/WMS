"""Seed a demo "Document Approval Workflow" that demonstrates a review/revise
retry loop: failed reviews route back to Request Changes, which loops back to
Review Document until it succeeds.

Run:
    python -m scripts.seed_document_approval

Safe to re-run: exits without creating duplicates if the workflow already exists.

Graph shape:

    Submit Document
          | SUCCESS
    Review Document
      /            \\
 SUCCESS          FAILURE
    |                 |
Publish Document  Request Changes
                      | SUCCESS (loop back)
                  Review Document
"""
import app.models  # noqa: F401  register ORM models before create_all
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Document Approval Workflow"

TASK_NAMES = [
    "Submit Document",
    "Review Document",
    "Publish Document",
    "Request Changes",
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
            print(
                f"'{DEMO_WORKFLOW_NAME}' already exists (id={existing.id}) — skipping seed."
            )
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
            db.add(
                WorkflowTransition(
                    workflow_id=workflow.id,
                    from_task_id=tasks[from_name].id,
                    to_task_id=tasks[to_name].id,
                    condition=condition,
                )
            )

        link("Submit Document",  "Review Document",  "SUCCESS")
        link("Review Document",  "Publish Document", "SUCCESS")
        link("Review Document",  "Request Changes",  "FAILURE")
        link("Request Changes",  "Review Document",  "SUCCESS")  # loop
        db.commit()

        print(
            f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) with "
            f"{len(tasks)} tasks and 4 transitions (including review/revise loop)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
