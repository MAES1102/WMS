"""HTTP boundary for the form-bounded workflow constructor."""

from collections.abc import Callable
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from app.application.constructor import (
    DraftTaskSpec,
    DraftTransitionSpec,
    WorkflowActivationRejected,
    WorkflowConstructorConflict,
    WorkflowConstructorService,
    WorkflowDraftNotFound,
    WorkflowDraftRejected,
    WorkflowDraftSpec,
)


class ConstructorTaskPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_key: str = Field(max_length=64)
    name: str = Field(max_length=120)
    task_type: str = Field(max_length=32)
    is_start: bool
    max_attempts: int | None = None


class ConstructorTransitionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_task_key: str = Field(max_length=64)
    to_task_key: str = Field(max_length=64)
    condition: str = Field(max_length=16)


class WorkflowDraftPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=120)
    tasks: list[ConstructorTaskPayload] = Field(max_length=64)
    transitions: list[ConstructorTransitionPayload] = Field(max_length=192)

    def to_spec(self) -> WorkflowDraftSpec:
        return WorkflowDraftSpec(
            name=self.name,
            tasks=tuple(
                DraftTaskSpec(
                    task_key=item.task_key,
                    name=item.name,
                    task_type=item.task_type,
                    is_start=item.is_start,
                    max_attempts=item.max_attempts,
                )
                for item in self.tasks
            ),
            transitions=tuple(
                DraftTransitionSpec(
                    from_task_key=item.from_task_key,
                    to_task_key=item.to_task_key,
                    condition=item.condition,
                )
                for item in self.transitions
            ),
        )


def create_constructor_router(
    service_dependency: Callable[..., WorkflowConstructorService],
) -> APIRouter:
    router = APIRouter(prefix="/api/workflows", tags=["workflow designer"])

    @router.get("/drafts")
    def list_drafts(
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> list[dict]:
        return jsonable_encoder([asdict(item) for item in service.list_drafts()])

    @router.post("/drafts", status_code=status.HTTP_201_CREATED)
    def create_draft(
        payload: WorkflowDraftPayload,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(service.create_draft(payload.to_spec())))
        except WorkflowDraftRejected as exc:
            raise _invalid_definition(exc) from exc
        except WorkflowConstructorConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    @router.post("/validate")
    def validate_spec(
        payload: WorkflowDraftPayload,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        return jsonable_encoder(asdict(service.validate_spec(payload.to_spec())))

    @router.get("/drafts/{draft_id}")
    def get_draft(
        draft_id: int,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(service.get_draft(draft_id)))
        except WorkflowDraftNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @router.put("/drafts/{draft_id}")
    def replace_draft(
        draft_id: int,
        payload: WorkflowDraftPayload,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(
                asdict(service.replace_draft(draft_id, payload.to_spec()))
            )
        except WorkflowDraftNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except WorkflowDraftRejected as exc:
            raise _invalid_definition(exc) from exc
        except WorkflowConstructorConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    @router.delete(
        "/drafts/{draft_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_draft(
        draft_id: int,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> None:
        try:
            service.delete_draft(draft_id)
        except WorkflowDraftNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except WorkflowConstructorConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    @router.post("/drafts/{draft_id}/validate")
    def validate_draft(
        draft_id: int,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(service.validate_draft(draft_id)))
        except WorkflowDraftNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @router.post("/drafts/{draft_id}/activate")
    def activate_draft(
        draft_id: int,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(service.activate_draft(draft_id)))
        except WorkflowDraftNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except WorkflowActivationRejected as exc:
            raise _invalid_definition(exc) from exc
        except WorkflowConstructorConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    @router.get("/revisions/{revision_id}")
    def get_revision(
        revision_id: int,
        service: WorkflowConstructorService = Depends(service_dependency),
    ) -> dict:
        try:
            return jsonable_encoder(asdict(service.get_revision(revision_id)))
        except WorkflowDraftNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return router


def _invalid_definition(exc: WorkflowDraftRejected) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        [asdict(issue) for issue in exc.issues],
    )
