"""Application service for an initial bounded invoice submission."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import BinaryIO, Protocol
from uuid import uuid4

from app.application.document_ports import DocumentStorage
from app.domain.invoice import RawInvoiceMetadata
from app.domain.types import ExecutionMode


class SubmissionUnavailable(RuntimeError):
    pass


class SubmissionConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class ActiveWorkflow:
    revision_id: int
    start_task_id: int


@dataclass(frozen=True)
class InvoiceSubmission:
    metadata: RawInvoiceMetadata
    original_filename: str
    declared_media_type: str
    document: BinaryIO
    mode: ExecutionMode


@dataclass(frozen=True)
class CreateSubmission:
    invoice_id: str
    run_id: str
    revision_id: int
    start_task_id: int
    mode: ExecutionMode
    metadata: RawInvoiceMetadata
    document_identity: str
    original_filename: str
    declared_media_type: str
    document_size_bytes: int
    created_at: datetime


@dataclass(frozen=True)
class SubmissionCreated:
    invoice_id: str
    run_id: str
    state_version: int


class SubmissionUnitOfWork(Protocol):
    def load_active_workflow(self) -> ActiveWorkflow:
        """Return the selected active revision and its single start task."""

    def create_submission(self, command: CreateSubmission) -> None:
        """Atomically create invoice, run, initial cursor, and trace."""


class InvoiceSubmissionService:
    def __init__(
        self,
        unit_of_work: SubmissionUnitOfWork,
        storage: DocumentStorage,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._storage = storage
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._clock = clock or (lambda: datetime.now(UTC))

    def submit(self, submission: InvoiceSubmission) -> SubmissionCreated:
        try:
            mode = ExecutionMode(submission.mode)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Unsupported execution mode {submission.mode!r}") from exc
        if len(submission.original_filename) > 255:
            raise ValueError("original_filename cannot exceed 255 characters")
        if not 1 <= len(submission.declared_media_type) <= 100:
            raise ValueError("declared_media_type length must be between 1 and 100")
        self._validate_raw_transport_bounds(submission.metadata)

        workflow = self._unit_of_work.load_active_workflow()
        stored = self._storage.store(submission.document)
        invoice_id = self._id_factory()
        run_id = self._id_factory()
        command = CreateSubmission(
            invoice_id=invoice_id,
            run_id=run_id,
            revision_id=workflow.revision_id,
            start_task_id=workflow.start_task_id,
            mode=mode,
            metadata=submission.metadata,
            document_identity=stored.identity,
            original_filename=submission.original_filename,
            declared_media_type=submission.declared_media_type,
            document_size_bytes=stored.size_bytes,
            created_at=self._clock(),
        )
        try:
            self._unit_of_work.create_submission(command)
        except BaseException:
            self._storage.delete(stored.identity)
            raise
        return SubmissionCreated(invoice_id, run_id, state_version=1)

    @staticmethod
    def _validate_raw_transport_bounds(metadata: RawInvoiceMetadata) -> None:
        bounds = {
            "supplier_name": (metadata.supplier_name, 512),
            "invoice_number": (metadata.invoice_number, 256),
            "issue_date": (metadata.issue_date, 32),
            "amount": (metadata.amount, 32),
            "currency": (metadata.currency, 16),
        }
        for field, (value, maximum) in bounds.items():
            if not isinstance(value, str) or len(value) > maximum:
                raise ValueError(
                    f"{field} raw value must be a string of at most "
                    f"{maximum} characters"
                )
