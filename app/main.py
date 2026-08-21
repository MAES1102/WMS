import app.persistence.models  # noqa: F401
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.presentation.approval_api import create_approval_router
from app.presentation.constructor_api import create_constructor_router
from app.presentation.runtime_api import create_runtime_router
from app.presentation.submission_api import create_submission_router
from app.runtime import (
    get_approval_queries,
    get_approval_service,
    get_constructor_service,
    get_execution_coordinator,
    get_run_queries,
    get_submission_service,
    initialize_purchase_request_runtime,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_purchase_request_runtime()
    yield


app = FastAPI(title="Event-Driven Workflow Management System", lifespan=lifespan)
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


@app.get("/ui", include_in_schema=False)
async def purchase_request_ui() -> FileResponse:
    return FileResponse(Path("app/static/index.html"))


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Event-Driven Workflow Management System running",
        "ui": "/ui",
        "api_docs": "/docs",
    }
