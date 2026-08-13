"""Read-only HTTP projection for one visible invoice run."""

from collections.abc import Callable
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.application.errors import StepStateError
from app.application.orchestration import InvoiceRunNotFound, InvoiceRunQueryService


def create_runtime_router(
    run_query_dependency: Callable[..., InvoiceRunQueryService],
) -> APIRouter:
    router = APIRouter(prefix="/api/v3", tags=["invoice-v3"])

    @router.get("/runs/{run_id}")
    def get_run(
        run_id: str,
        queries: InvoiceRunQueryService = Depends(run_query_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(queries.get(run_id)))
        except InvoiceRunNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except StepStateError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return router
