from app.application.invoice_validation import (
    DocumentValidationEffectPolicy,
    DocumentValidationExecutor,
    InvoiceValidationInput,
    MAX_PDF_BYTES,
    PdfInspection,
    PdfInspectionError,
)
from app.application.ports import (
    ExecutionContext,
    InvoiceMetadataValidated,
    InvoiceStateChanged,
)
from app.domain.invoice import InvoiceState, RawInvoiceMetadata
from app.domain.types import FailureClass, TaskOutcome, TaskResult, TaskType


class FakeSource:
    def __init__(self, value: InvoiceValidationInput) -> None:
        self.value = value

    def load(self, _context: ExecutionContext) -> InvoiceValidationInput:
        return self.value


class FakeInspector:
    def __init__(
        self,
        result: PdfInspection | None = None,
        error: str | None = None,
    ) -> None:
        self.result = result or PdfInspection(page_count=1)
        self.error = error
        self.calls: list[str] = []

    def inspect(self, identity: str) -> PdfInspection:
        self.calls.append(identity)
        if self.error is not None:
            raise PdfInspectionError(self.error)
        return self.result


def context(task_type: TaskType = TaskType.DOCUMENT_VALIDATION) -> ExecutionContext:
    return ExecutionContext(
        run_id="run-1",
        invoice_id="invoice-1",
        task_id=1,
        task_type=task_type,
        attempt_ordinal=1,
    )


def value(**changes) -> InvoiceValidationInput:
    values = {
        "metadata": RawInvoiceMetadata(
            "Supplier",
            "INV-1",
            "2026-08-13",
            "12.34",
            "EUR",
        ),
        "document_identity": "a" * 32,
        "declared_media_type": "application/pdf",
        "document_size_bytes": 100,
    }
    values.update(changes)
    return InvoiceValidationInput(**values)


def test_valid_metadata_and_pdf_return_success() -> None:
    inspector = FakeInspector(PdfInspection(page_count=2))
    executor = DocumentValidationExecutor(FakeSource(value()), inspector)

    result = executor.execute(context())

    assert result.outcome is TaskOutcome.SUCCESS
    assert result.failure_class is None
    assert inspector.calls == ["a" * 32]


def test_validation_effect_policy_normalizes_success_metadata() -> None:
    source = FakeSource(
        value(
            metadata=RawInvoiceMetadata(
                " Supplier ", " INV-1 ", "2026-08-13", "12.34", "EUR"
            )
        )
    )

    effects = DocumentValidationEffectPolicy(source).effects_for(
        context(),
        TaskResult(TaskOutcome.SUCCESS),
    )

    assert len(effects) == 1
    assert isinstance(effects[0], InvoiceMetadataValidated)
    assert effects[0].metadata.supplier_name == "Supplier"
    assert effects[0].metadata.invoice_number == "INV-1"


def test_invalid_metadata_and_media_return_complete_business_failure() -> None:
    inspector = FakeInspector()
    invalid = value(
        metadata=RawInvoiceMetadata(" ", " ", "bad", "0", "eur"),
        declared_media_type="text/plain",
        document_size_bytes=0,
    )
    executor = DocumentValidationExecutor(FakeSource(invalid), inspector)

    result = executor.execute(context())

    assert result.outcome is TaskOutcome.FAILURE
    assert result.failure_class is FailureClass.BUSINESS
    assert "supplier_name:" in result.reason
    assert "invoice_number:" in result.reason
    assert "issue_date:" in result.reason
    assert "amount:" in result.reason
    assert "currency:" in result.reason
    assert "declared media type" in result.reason
    assert "size must be" in result.reason
    assert inspector.calls == []


def test_validation_effect_policy_marks_business_failure() -> None:
    result = TaskResult(
        TaskOutcome.FAILURE,
        FailureClass.BUSINESS,
        "amount: must be positive",
    )

    effects = DocumentValidationEffectPolicy(FakeSource(value())).effects_for(
        context(), result
    )

    assert effects == (
        InvoiceStateChanged(
            InvoiceState.VALIDATION_FAILED,
            "amount: must be positive",
        ),
    )


def test_pdf_library_failure_is_a_visible_business_failure() -> None:
    inspector = FakeInspector(error="PDF is malformed or unreadable")
    executor = DocumentValidationExecutor(FakeSource(value()), inspector)

    result = executor.execute(context())

    assert result.outcome is TaskOutcome.FAILURE
    assert result.failure_class is FailureClass.BUSINESS
    assert result.reason == "document: PDF is malformed or unreadable"


def test_oversize_and_wrong_task_type_are_controlled() -> None:
    inspector = FakeInspector()
    executor = DocumentValidationExecutor(
        FakeSource(value(document_size_bytes=MAX_PDF_BYTES + 1)),
        inspector,
    )

    result = executor.execute(context())
    assert result.outcome is TaskOutcome.FAILURE
    assert "size must be" in result.reason
    assert inspector.calls == []

    try:
        executor.execute(context(TaskType.ARCHIVE_DOCUMENT))
    except ValueError as exc:
        assert "requires DOCUMENT_VALIDATION" in str(exc)
    else:
        raise AssertionError("wrong executor task type must be rejected")
