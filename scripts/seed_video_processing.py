"""Seed "Video Streaming Processing" — media-processing sequential workflow.

Demonstrates: a strictly ordered media pipeline where each processing stage
must complete before the next begins. Virus Scan failure routes to Quarantine
Video instead of processing infected content.

Graph shape:

    Upload Video
          | SUCCESS
    Virus Scan
     /        \\
SUCCESS      FAILURE
   |             |
Extract Metadata  Quarantine Video
   | SUCCESS
Convert Resolution
   | SUCCESS
Generate Thumbnail
   | SUCCESS
Upload To CDN
   | SUCCESS
Notify Creator

Run:
    python -m scripts.seed_video_processing
"""
import app.models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.models import Task, User, Workflow, WorkflowTransition

DEMO_EMAIL = "demo@payment.com"
DEMO_WORKFLOW_NAME = "Video Streaming Processing"

TASK_NAMES = [
    "Upload Video",
    "Virus Scan",
    "Extract Metadata",
    "Convert Resolution",
    "Generate Thumbnail",
    "Upload To CDN",
    "Notify Creator",
    "Quarantine Video",      # FAILURE branch from Virus Scan
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

        link("Upload Video",       "Virus Scan",           "SUCCESS")
        link("Virus Scan",         "Extract Metadata",     "SUCCESS")
        link("Virus Scan",         "Quarantine Video",     "FAILURE")
        link("Extract Metadata",   "Convert Resolution",   "SUCCESS")
        link("Convert Resolution", "Generate Thumbnail",   "SUCCESS")
        link("Generate Thumbnail", "Upload To CDN",        "SUCCESS")
        link("Upload To CDN",      "Notify Creator",       "SUCCESS")
        db.commit()

        print(f"Seeded '{DEMO_WORKFLOW_NAME}' (workflow_id={workflow.id}) "
              f"with {len(tasks)} tasks and 7 transitions.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
