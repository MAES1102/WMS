"""Separate v3 HTTP boundary for persistent approval work."""

from collections.abc import Callable
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.application.approval import (
    ApprovalDecisionConflict,
    ApprovalNotFound,
    ApprovalQueryService,
    HumanApprovalService,
)
from app.application.errors import StateVersionConflict, StepStateError
from app.application.orchestration import (
    InvoiceExecutionCoordinator,
    InvoiceRunQueryService,
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
    service_dependency: Callable[..., HumanApprovalService],
    query_dependency: Callable[..., ApprovalQueryService],
    coordinator_dependency: Callable[..., InvoiceExecutionCoordinator] | None = None,
    run_query_dependency: Callable[..., InvoiceRunQueryService] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v3/approvals", tags=["approval-v3"])
    coordinator_provider = coordinator_dependency or (lambda: None)
    run_query_provider = run_query_dependency or (lambda: None)

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
        service: HumanApprovalService = Depends(service_dependency),
        coordinator: InvoiceExecutionCoordinator | None = Depends(
            coordinator_provider
        ),
        run_queries: InvoiceRunQueryService | None = Depends(
            run_query_provider
        ),
    ) -> dict:
        try:
            value = ApprovalDecisionInput(
                choice=payload.choice,
                note=payload.note,
                reason=payload.reason,
            )
            if coordinator is None:
                accepted = service.decide(
                    work_item_id,
                    value,
                    expected_state_version=payload.expected_state_version,
                )
                execution = None
            else:
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
        response = {
            "work_item_id": accepted.work_item_id,
            "run_id": accepted.run_id,
            "outcome": accepted.outcome.value,
            "state_version": accepted.committed_state_version,
            "replayed": accepted.replayed,
            "resume_required": not accepted.replayed,
        }
        if execution is not None:
            if run_queries is None:
                raise RuntimeError(
                    "A run query dependency is required with the coordinator"
                )
            response["execution_phase"] = execution.phase.value
            response["run"] = jsonable_encoder(
                asdict(run_queries.get(accepted.run_id))
            )
        return response

    return router
