"""Seed "Banking Transaction Workflow" — ACID-like fail-fast flow.

Demonstrates: strict sequential execution where any failure stops the chain.
Transfer Money has a FAILURE branch to Rollback Transaction — a realistic
compensating transaction pattern that prevents partial state.

Without WorkflowTransition rows this would be the legacy sequential executor.
With explicit SUCCESS/FAILURE edges the graph engine handles routing, making
the fail-fast and rollback semantics visible in the UI.

Graph shape:

    Authenticate User
          | SUCCESS
    Validate Account Balance
          | SUCCESS
    Fraud Detection
          | SUCCESS
    Lock Transaction
          | SUCCESS
    Transfer Money
     /           \\
SUCCESS         FAILURE
   |               |
Update Ledger  Rollback Transaction
   | SUCCESS
Send Notification

Run:
    python -m scripts.seed_banking_transaction
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Banking Transaction Workflow"

TASK_NAMES = [
    "Authenticate User",
    "Validate Account Balance",
    "Fraud Detection",
    "Lock Transaction",
    "Transfer Money",
    "Update Ledger",
    "Send Notification",
    "Rollback Transaction",   # compensating transaction on failure
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

        # Strict sequential happy path
        link("Authenticate User",         "Validate Account Balance", "SUCCESS")
        link("Validate Account Balance",  "Fraud Detection",          "SUCCESS")
        link("Fraud Detection",           "Lock Transaction",         "SUCCESS")
        link("Lock Transaction",          "Transfer Money",           "SUCCESS")
        # Compensating transaction: failure → rollback instead of continuing
        link("Transfer Money",            "Update Ledger",            "SUCCESS")
        link("Transfer Money",            "Rollback Transaction",     "FAILURE")
        link("Update Ledger",             "Send Notification",        "SUCCESS")
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and 7 transitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
