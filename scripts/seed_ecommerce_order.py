"""Seed "E-Commerce Order Processing" — long sequential graph with branching.

Demonstrates: multi-step business workflow, happy-path SUCCESS chain, and a
FAILURE branch from Fraud Detection that routes to Cancel Order instead of
continuing to payment — a realistic decision gateway.

Graph shape:

    Receive Order
          | SUCCESS
    Validate Customer
          | SUCCESS
    Fraud Detection
     /           \\
SUCCESS         FAILURE
   |               |
Process Payment  Cancel Order
   | SUCCESS
Reserve Inventory
   | SUCCESS
Generate Invoice
   | SUCCESS
Send Confirmation Email
   | SUCCESS
Prepare Shipment

Run:
    python -m scripts.seed_ecommerce_order
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "E-Commerce Order Processing"

TASK_NAMES = [
    "Receive Order",
    "Validate Customer Information",
    "Fraud Detection Check",
    "Process Payment",
    "Reserve Inventory",
    "Generate Invoice",
    "Send Confirmation Email",
    "Prepare Shipment",
    "Cancel Order",            # FAILURE terminal for Fraud Detection
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

        # Happy path: straight SUCCESS chain
        link("Receive Order",             "Validate Customer Information", "SUCCESS")
        link("Validate Customer Information", "Fraud Detection Check",    "SUCCESS")
        # Decision gateway: SUCCESS → payment, FAILURE → cancel
        link("Fraud Detection Check",     "Process Payment",              "SUCCESS")
        link("Fraud Detection Check",     "Cancel Order",                 "FAILURE")
        link("Process Payment",           "Reserve Inventory",            "SUCCESS")
        link("Reserve Inventory",         "Generate Invoice",             "SUCCESS")
        link("Generate Invoice",          "Send Confirmation Email",      "SUCCESS")
        link("Send Confirmation Email",   "Prepare Shipment",             "SUCCESS")
        db.commit()

        n_trans = 8
        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and {n_trans} transitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
