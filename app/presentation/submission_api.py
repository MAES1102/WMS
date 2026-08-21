"""JSON HTTP boundary for structured Purchase Request submission."""

from collections.abc import Callable
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from app.application.errors import StateVersionConflict, StepStateError
from app.application.orchestration import PurchaseRequestExecutionCoordinator, PurchaseRequestRunQueryService
from app.application.submission import PurchaseRequestSubmission, PurchaseRequestSubmissionService, SubmissionConflict, SubmissionUnavailable
from app.domain.purchase_request import RawPurchaseRequest
from app.domain.types import DemoScenario, ExecutionMode


class PurchaseRequestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requester_name: str = Field(max_length=512)
    department: str = Field(max_length=512)
    item_or_service: str = Field(max_length=1024)
    supplier: str = Field(max_length=512)
    amount: str = Field(max_length=32)
    currency: str = Field(max_length=16)
    business_justification: str = Field(max_length=2000)
    required_date: str = Field(max_length=32)
    execution_mode: ExecutionMode = ExecutionMode.ORCHESTRATION
    demonstration_scenario: DemoScenario = DemoScenario.STANDARD


def create_submission_router(service_dependency: Callable[..., PurchaseRequestSubmissionService], coordinator_dependency: Callable[..., PurchaseRequestExecutionCoordinator], run_query_dependency: Callable[..., PurchaseRequestRunQueryService]) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["purchase requests"])

    @router.post("/requests", status_code=status.HTTP_201_CREATED)
    def submit_request(payload: PurchaseRequestPayload, service=Depends(service_dependency), coordinator=Depends(coordinator_dependency), queries=Depends(run_query_dependency)) -> dict:
        try:
            created = service.submit(PurchaseRequestSubmission(
                RawPurchaseRequest(payload.requester_name, payload.department, payload.item_or_service, payload.supplier, payload.amount, payload.currency, payload.business_justification, payload.required_date),
                payload.execution_mode, payload.demonstration_scenario,
            ))
            execution = coordinator.drive(created.run_id)
            response = jsonable_encoder(asdict(queries.get(created.run_id)))
            response["work_item_id"] = execution.work_item_id
            return response
        except (ValueError, SubmissionUnavailable) as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        except (SubmissionConflict, StateVersionConflict, StepStateError) as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return router
