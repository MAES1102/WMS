"""Bounded multipart HTTP adapter for invoice submission."""

from collections.abc import Callable
from dataclasses import asdict
from email.parser import BytesParser
from email.policy import default
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder

from app.application.document_ports import DocumentStorageBoundaryError
from app.application.invoice_validation import MAX_PDF_BYTES
from app.application.errors import StateVersionConflict, StepStateError
from app.application.orchestration import (
    InvoiceExecutionCoordinator,
    InvoiceRunQueryService,
)
from app.application.submission import (
    InvoiceSubmission,
    InvoiceSubmissionService,
    SubmissionConflict,
    SubmissionUnavailable,
)
from app.domain.invoice import RawInvoiceMetadata
from app.domain.types import ExecutionMode


_MAX_MULTIPART_BYTES = MAX_PDF_BYTES + 65_536
_TEXT_FIELDS = (
    "supplier_name",
    "invoice_number",
    "issue_date",
    "amount",
    "currency",
    "mode",
)


class MultipartSubmissionError(ValueError):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def parse_invoice_submission(request: Request) -> InvoiceSubmission:
    content_type = request.headers.get("content-type", "")
    if not content_type.lower().startswith("multipart/form-data"):
        raise MultipartSubmissionError(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Content-Type must be multipart/form-data",
        )
    declared_length = request.headers.get("content-length")
    if declared_length is not None:
        try:
            length = int(declared_length)
        except ValueError as exc:
            raise MultipartSubmissionError(
                status.HTTP_400_BAD_REQUEST,
                "Content-Length must be an integer",
            ) from exc
        if length > _MAX_MULTIPART_BYTES:
            raise MultipartSubmissionError(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "Multipart request exceeds the bounded submission size",
            )

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > _MAX_MULTIPART_BYTES:
            raise MultipartSubmissionError(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "Multipart request exceeds the bounded submission size",
            )

    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: "
        + content_type.encode("ascii", errors="strict")
        + b"\r\nMIME-Version: 1.0\r\n\r\n"
        + bytes(body)
    )
    if not message.is_multipart():
        raise MultipartSubmissionError(
            status.HTTP_400_BAD_REQUEST,
            "Malformed multipart request",
        )

    values: dict[str, str] = {}
    document: bytes | None = None
    original_filename: str | None = None
    document_media_type: str | None = None
    for part in message.iter_parts():
        if part.is_multipart():
            raise MultipartSubmissionError(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Nested multipart fields are not accepted",
            )
        name = part.get_param("name", header="content-disposition")
        if not name:
            raise MultipartSubmissionError(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Every multipart field requires a name",
            )
        payload = part.get_payload(decode=True) or b""
        if name == "document":
            if document is not None:
                raise MultipartSubmissionError(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Exactly one document field is required",
                )
            document = payload
            original_filename = part.get_filename()
            document_media_type = part.get_content_type()
            continue
        if name not in _TEXT_FIELDS:
            raise MultipartSubmissionError(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Unsupported multipart field {name!r}",
            )
        if name in values:
            raise MultipartSubmissionError(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Multipart field {name!r} must occur once",
            )
        try:
            values[name] = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MultipartSubmissionError(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Multipart field {name!r} must be UTF-8 text",
            ) from exc

    missing = [name for name in _TEXT_FIELDS if name not in values]
    if missing or document is None:
        required = missing + (["document"] if document is None else [])
        raise MultipartSubmissionError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Missing required multipart fields: " + ", ".join(required),
        )
    if not original_filename:
        raise MultipartSubmissionError(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "The document field requires an original filename",
        )
    assert document_media_type is not None
    return InvoiceSubmission(
        metadata=RawInvoiceMetadata(
            supplier_name=values["supplier_name"],
            invoice_number=values["invoice_number"],
            issue_date=values["issue_date"],
            amount=values["amount"],
            currency=values["currency"],
        ),
        original_filename=original_filename,
        declared_media_type=document_media_type,
        document=BytesIO(document),
        mode=ExecutionMode(values["mode"]),
    )


def create_submission_router(
    service_dependency: Callable[..., InvoiceSubmissionService],
    coordinator_dependency: Callable[..., InvoiceExecutionCoordinator] | None = None,
    run_query_dependency: Callable[..., InvoiceRunQueryService] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v3", tags=["invoice-v3"])
    coordinator_provider = coordinator_dependency or (lambda: None)
    query_provider = run_query_dependency or (lambda: None)

    @router.post("/invoices", status_code=status.HTTP_201_CREATED)
    async def submit_invoice(
        request: Request,
        service: InvoiceSubmissionService = Depends(service_dependency),
        coordinator: InvoiceExecutionCoordinator | None = Depends(
            coordinator_provider
        ),
        queries: InvoiceRunQueryService | None = Depends(query_provider),
    ) -> dict:
        try:
            submission = await parse_invoice_submission(request)
            created = service.submit(submission)
        except MultipartSubmissionError as exc:
            raise HTTPException(exc.status_code, exc.detail) from exc
        except DocumentStorageBoundaryError as exc:
            code = (
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                if "exceeds" in str(exc)
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            )
            raise HTTPException(code, str(exc)) from exc
        except (ValueError, UnicodeError) as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                str(exc),
            ) from exc
        except SubmissionUnavailable as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        except SubmissionConflict as exc:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                str(exc),
            ) from exc
        if coordinator is not None:
            if queries is None:
                raise RuntimeError(
                    "A run query dependency is required with the coordinator"
                )
            try:
                execution = coordinator.drive(created.run_id)
                view = queries.get(created.run_id)
            except (StateVersionConflict, StepStateError) as exc:
                raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
            response = jsonable_encoder(asdict(view))
            response["work_item_id"] = execution.work_item_id
            return response
        return {
            "invoice_id": created.invoice_id,
            "run_id": created.run_id,
            "invoice_state": "SUBMITTED",
            "run_status": "RUNNING",
            "state_version": created.state_version,
        }

    return router
