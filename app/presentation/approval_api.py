"""HTTP boundary for persistent approval work."""

from collections.abc import Callable
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.application.approval import (
    ApprovalDecisionConflict,
    ApprovalNotFound,
    ApprovalQueryService,
)
from app.application.errors import StateVersionConflict, StepStateError
from app.application.orchestration import (
    PurchaseRequestExecutionCoordinator,
    PurchaseRequestRunQueryService,
)
from app.domain.approval import (
    ApprovalDecisionError,
    ApprovalDecisionInput,
)


class ApprovalDecisionPayload(BaseModel):
    choice: str
    note: str | None = None
    reason: str | None = None
    expected_state_version: int | None = None


def create_approval_router(
    query_dependency: Callable[..., ApprovalQueryService],
    coordinator_dependency: Callable[..., PurchaseRequestExecutionCoordinator],
    run_query_dependency: Callable[..., PurchaseRequestRunQueryService],
) -> APIRouter:
    router = APIRouter(prefix="/api/approvals", tags=["approvals"])

    @router.get("")
    def list_pending(
        queries: ApprovalQueryService = Depends(query_dependency),
    ) -> list[dict]:
        return [asdict(item) for item in queries.list_pending()]

    @router.get("/{work_item_id}")
    def get_approval(
        work_item_id: str,
        queries: ApprovalQueryService = Depends(query_dependency),
    ) -> dict:
        try:
            return asdict(queries.get(work_item_id))
        except ApprovalNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @router.post("/{work_item_id}/decision")
    def decide(
        work_item_id: str,
        payload: ApprovalDecisionPayload,
        coordinator: PurchaseRequestExecutionCoordinator = Depends(coordinator_dependency),
        run_queries: PurchaseRequestRunQueryService = Depends(run_query_dependency),
    ) -> dict:
        try:
            value = ApprovalDecisionInput(
                choice=payload.choice,
                note=payload.note,
                reason=payload.reason,
            )
            resumed = coordinator.decide_and_resume(
                work_item_id,
                value,
                expected_state_version=payload.expected_state_version,
            )
            accepted = resumed.decision
            execution = resumed.execution
        except ApprovalNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ApprovalDecisionError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                str(exc),
            ) from exc
        except (ApprovalDecisionConflict, StateVersionConflict, StepStateError) as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        return {
            "work_item_id": accepted.work_item_id,
            "run_id": accepted.run_id,
            "outcome": accepted.outcome.value,
            "state_version": accepted.committed_state_version,
            "replayed": accepted.replayed,
            "resume_required": not accepted.replayed,
            "execution_phase": execution.phase.value,
            "run": jsonable_encoder(asdict(run_queries.get(accepted.run_id))),
        }

    return router
