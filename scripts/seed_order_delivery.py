"""Seed a demo "Order Delivery Workflow" that demonstrates conditional branching
on inventory check result.

Run:
    python -m scripts.seed_order_delivery

Safe to re-run: exits without creating duplicates if the workflow already exists.

Graph shape:

    Receive Order
          | SUCCESS
    Check Inventory
      /            \\
 SUCCESS          FAILURE
    |                 |
Package Order    Notify Customer
    | SUCCESS
  Ship Order
"""
import app.models  # noqa: F401  register ORM models before create_all
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Order Delivery Workflow"

TASK_NAMES = [
    "Receive Order",
    "Check Inventory",
    "Package Order",
    "Ship Order",
    "Notify Customer",
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

        link("Receive Order",    "Check Inventory",  "SUCCESS")
        link("Check Inventory",  "Package Order",    "SUCCESS")
        link("Check Inventory",  "Notify Customer",  "FAILURE")
        link("Package Order",    "Ship Order",       "SUCCESS")
        db.commit()

        print(
            f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) with "
            f"{len(tasks)} tasks and 4 transitions."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
