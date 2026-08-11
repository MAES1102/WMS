import app.models  # noqa: F401  # регистрируем ORM модели до create_all (иначе таблицы не создадутся)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.db import Base, engine
from app.routes import router


def _apply_schema_migrations(eng) -> None:
    """Idempotent column-level migrations for the dev SQLite database.

    ``create_all`` only creates *new* tables — it never adds columns to
    existing ones.  This function fills the gap so that a database created
    before a schema change stays in sync without requiring Alembic.

    Safe to call on every startup: each statement is guarded by an existence
    check and only runs when the column is actually missing.
    """
    insp = inspect(eng)
    with eng.connect() as conn:
        # workflow_runs.created_at — added in WorkflowRun+TaskExecution migration
        existing = {c["name"] for c in insp.get_columns("workflow_runs")}
        if "created_at" not in existing:
            conn.execute(text(
                "ALTER TABLE workflow_runs ADD COLUMN created_at DATETIME"
            ))
            conn.commit()


# lifecycle FastAPI: startup/shutdown в одном месте (замена on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # на startup создаём схему БД из metadata всех моделей
    Base.metadata.create_all(bind=engine)
    # add any columns missing from pre-migration databases
    _apply_schema_migrations(engine)
    yield


app = FastAPI(title="Workflow Automation", lifespan=lifespan)
app.include_router(router)  # отделяем маршруты от точки входа (модульность)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Workflow system running"}
