"""Read-only HTTP projection for one visible purchase_request run."""

from collections.abc import Callable
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.application.errors import StepStateError
from app.application.orchestration import PurchaseRequestRunNotFound, PurchaseRequestRunQueryService


def create_runtime_router(
    run_query_dependency: Callable[..., PurchaseRequestRunQueryService],
) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["runs"])

    @router.get("/runs/{run_id}")
    def get_run(
        run_id: str,
        queries: PurchaseRequestRunQueryService = Depends(run_query_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(queries.get(run_id)))
        except PurchaseRequestRunNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except StepStateError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return router
