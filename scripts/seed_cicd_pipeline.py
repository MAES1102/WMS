"""Seed "CI/CD Deployment Pipeline" — software-engineering workflow with quality gates.

Demonstrates: conditional routing after each quality gate. Failures in testing
or security scan route to "Pipeline Failed" (a safe terminal node) rather than
continuing to production — mirroring real CI/CD fail-fast gates.

Graph shape:

    Pull Source Code
          | SUCCESS
    Install Dependencies
          | SUCCESS
    Run Unit Tests
     /           \\
SUCCESS         FAILURE
   |               |
Run Integration Tests  Pipeline Failed
     /           \\
SUCCESS         FAILURE
   |               |
Security Scan   Pipeline Failed
     /           \\
SUCCESS         FAILURE
   |               |
Build Docker Image  Pipeline Failed
     | SUCCESS
Deploy Application
     | SUCCESS
Health Check

Run:
    python -m scripts.seed_cicd_pipeline
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "CI/CD Deployment Pipeline"

TASK_NAMES = [
    "Pull Source Code",
    "Install Dependencies",
    "Run Unit Tests",
    "Run Integration Tests",
    "Security Scan",
    "Build Docker Image",
    "Deploy Application",
    "Health Check",
    "Pipeline Failed",         # terminal node for any quality-gate failure
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

        # Initial steps — must succeed to proceed
        link("Pull Source Code",      "Install Dependencies",  "SUCCESS")
        link("Install Dependencies",  "Run Unit Tests",        "SUCCESS")

        # Quality gate 1: unit tests
        link("Run Unit Tests",        "Run Integration Tests", "SUCCESS")
        link("Run Unit Tests",        "Pipeline Failed",       "FAILURE")

        # Quality gate 2: integration tests
        link("Run Integration Tests", "Security Scan",         "SUCCESS")
        link("Run Integration Tests", "Pipeline Failed",       "FAILURE")

        # Quality gate 3: security scan
        link("Security Scan",         "Build Docker Image",    "SUCCESS")
        link("Security Scan",         "Pipeline Failed",       "FAILURE")

        # Build and deploy
        link("Build Docker Image",    "Deploy Application",    "SUCCESS")
        link("Deploy Application",    "Health Check",          "SUCCESS")
        db.commit()

        n_trans = 10
        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and {n_trans} transitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
