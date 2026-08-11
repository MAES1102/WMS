"""Seed "BUG-02 Demonstration" — shows why conditional event publishing matters.

Demonstrates the BUG-02 fix: in choreography mode, task_completed events are
only published on SUCCESS. If Initial Validation fails, the event is NOT emitted,
so Dangerous Operation never starts — regardless of mode.

This workflow intentionally has NO WorkflowTransition rows so it runs via the
legacy sequential executor. The sequential path is the clearest demonstration of
BUG-02 semantics:

  Orchestration:
    Task 1 FAILED → workflow.status = "failed" → stops → Task 2 never runs.

  Choreography (legacy sequential):
    Task 1 FAILED → no task_completed event published (BUG-02 fix) →
    Task 2 handler never triggered → workflow stops.

  Without the fix (original bug):
    Task 1 FAILED → event published anyway → Task 2 starts → DANGEROUS.

Graph shape (no transitions — legacy sequential by order):

    [1] Initial Validation
    [2] Dangerous Operation That Must NOT Execute
    [3] Final Step

Run:
    python -m scripts.seed_bug02_demo
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "BUG-02 Demonstration"

TASK_NAMES = [
    "Initial Validation",
    "Dangerous Operation That Must NOT Execute",
    "Final Step",
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

        for order, name in enumerate(TASK_NAMES, start=1):
            task = Task(name=name, workflow_id=workflow.id, order=order)
            db.add(task)
            db.commit()
            db.refresh(task)

        # Intentionally NO WorkflowTransition rows.
        # Uses legacy sequential executor (execution_order 1→2→3).
        # The engine's BUG-02 fix ensures Task 2 never runs if Task 1 fails.
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(TASK_NAMES)} tasks and 0 transitions "
              f"(legacy sequential — BUG-02 demonstration).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
