import app.models  # noqa: F401
import app.persistence.models  # noqa: F401
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.routes import router
from app.presentation.approval_api import create_approval_router
from app.presentation.constructor_api import create_constructor_router
from app.presentation.runtime_api import create_runtime_router
from app.presentation.submission_api import create_submission_router
from app.v3_runtime import (
    get_approval_queries,
    get_approval_service,
    get_constructor_service,
    get_execution_coordinator,
    get_run_queries,
    get_submission_service,
    initialize_invoice_runtime,
)


_LEGACY_TABLE_NAMES = {
    "users",
    "workflows",
    "workflow_runs",
    "tasks",
    "workflow_transitions",
    "task_attempts",
    "trace_entries",
}
_LEGACY_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name in _LEGACY_TABLE_NAMES
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine, tables=_LEGACY_TABLES)
    initialize_invoice_runtime()
    yield


app = FastAPI(title="Invoice Workflow Automation", lifespan=lifespan)
app.include_router(router)
app.include_router(
    create_submission_router(
        get_submission_service,
        coordinator_dependency=get_execution_coordinator,
        run_query_dependency=get_run_queries,
    )
)
app.include_router(
    create_approval_router(
        get_approval_service,
        get_approval_queries,
        coordinator_dependency=get_execution_coordinator,
        run_query_dependency=get_run_queries,
    )
)
app.include_router(create_runtime_router(get_run_queries))
app.include_router(create_constructor_router(get_constructor_service))
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Invoice workflow system running",
        "ui": "/ui",
        "api_docs": "/docs",
    }
