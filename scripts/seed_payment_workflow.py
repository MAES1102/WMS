"""Seed a demo "Payment Workflow" that exercises the full BPMN-like graph
engine: a decision gateway (Fraud Check), a failure/cancel branch, and a
retry loop (Capture Payment <-> Retry Payment).

Run:
    python -m scripts.seed_payment_workflow

Safe to re-run: if the workflow already exists for the demo user, the
script exits without creating duplicates.

Graph shape:

    Create Payment
          | SUCCESS
    Validate Card
          | SUCCESS
     Fraud Check
      /          \\
 SUCCESS        FAILURE
    |               |
Capture Payment  Cancel Payment
    |  \\
    |   FAILURE -> Retry Payment --SUCCESS--> Capture Payment (loop)
    | SUCCESS
Send Receipt
"""
import app.models  # noqa: F401  register ORM models before create_all
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Payment Workflow"

TASK_NAMES = [
    "Create Payment",
    "Validate Card",
    "Fraud Check",
    "Capture Payment",
    "Retry Payment",
    "Cancel Payment",
    "Send Receipt",
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
                f"Payment Workflow already exists (id={existing.id}) — skipping seed."
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

        link("Create Payment", "Validate Card", "SUCCESS")
        link("Validate Card", "Fraud Check", "SUCCESS")
        link("Fraud Check", "Capture Payment", "SUCCESS")
        link("Fraud Check", "Cancel Payment", "FAILURE")
        link("Capture Payment", "Retry Payment", "FAILURE")
        link("Retry Payment", "Capture Payment", "SUCCESS")
        link("Capture Payment", "Send Receipt", "SUCCESS")
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) with "
              f"{len(tasks)} tasks and 7 transitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
