"""DOCUMENT_VALIDATION executor and its document-facing ports."""

from dataclasses import dataclass
from typing import Protocol

from app.application.ports import (
    ExecutionContext,
    InvoiceMetadataValidated,
    InvoiceStateChanged,
    StepEffect,
    StepResolution,
)
from app.domain.invoice import (
    InvoiceState,
    InvoiceMetadataError,
    RawInvoiceMetadata,
    validate_invoice_metadata,
)
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


MAX_PDF_BYTES = 10_485_760


@dataclass(frozen=True)
class InvoiceValidationInput:
    metadata: RawInvoiceMetadata
    document_identity: str
    declared_media_type: str
    document_size_bytes: int


@dataclass(frozen=True)
class PdfInspection:
    page_count: int


class PdfInspectionError(ValueError):
    pass


class InvoiceValidationSource(Protocol):
    def load(self, context: ExecutionContext) -> InvoiceValidationInput:
        """Load raw invoice and controlled document metadata for one run."""


class PdfInspector(Protocol):
    def inspect(self, document_identity: str) -> PdfInspection:
        """Inspect one controlled stored document without text extraction."""


class DocumentValidationExecutor:
    def __init__(
        self,
        source: InvoiceValidationSource,
        pdf_inspector: PdfInspector,
    ) -> None:
        self._source = source
        self._pdf_inspector = pdf_inspector

    def execute(self, context: ExecutionContext) -> TaskResult:
        if context.task_type is not TaskType.DOCUMENT_VALIDATION:
            raise ValueError(
                "DocumentValidationExecutor requires DOCUMENT_VALIDATION"
            )

        value = self._source.load(context)
        reasons: list[str] = []
        try:
            validate_invoice_metadata(value.metadata)
        except InvoiceMetadataError as exc:
            reasons.extend(
                f"{issue.field}: {issue.detail}" for issue in exc.issues
            )

        if value.declared_media_type != "application/pdf":
            reasons.append("document: declared media type must be application/pdf")
        if not 1 <= value.document_size_bytes <= MAX_PDF_BYTES:
            reasons.append(
                "document: size must be between 1 and 10485760 bytes"
            )

        if not reasons:
            try:
                inspection = self._pdf_inspector.inspect(value.document_identity)
            except PdfInspectionError as exc:
                reasons.append(f"document: {exc}")
            else:
                if inspection.page_count < 1:
                    reasons.append("document: PDF must contain at least one page")

        if reasons:
            return TaskResult(
                outcome=TaskOutcome.FAILURE,
                failure_class=FailureClass.BUSINESS,
                reason="; ".join(reasons),
            )
        return TaskResult(outcome=TaskOutcome.SUCCESS)


class DocumentValidationEffectPolicy:
    """Translate validation results into persistence-neutral invoice effects."""

    def __init__(self, source: InvoiceValidationSource) -> None:
        self._source = source

    def effects_for(
        self,
        context: ExecutionContext,
        result: TaskResult,
        _resolution: StepResolution | None = None,
    ) -> tuple[StepEffect, ...]:
        if context.task_type is not TaskType.DOCUMENT_VALIDATION:
            return ()
        if result.outcome is TaskOutcome.SUCCESS:
            value = self._source.load(context)
            return (
                InvoiceMetadataValidated(
                    validate_invoice_metadata(value.metadata)
                ),
            )
        if result.failure_class is FailureClass.BUSINESS:
            return (
                InvoiceStateChanged(
                    state=InvoiceState.VALIDATION_FAILED,
                    reason=result.reason,
                ),
            )
        return ()
