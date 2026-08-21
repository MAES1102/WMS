from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.application.invoice_validation import MAX_PDF_BYTES, PdfInspectionError
from app.infrastructure.documents import (
    DocumentBoundaryError,
    LocalDocumentStorage,
)
from app.infrastructure.pdf import PypdfInspector


def pdf_bytes(*, pages: int = 1, password: str | None = None) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    if password is not None:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_storage_uses_generated_identity_and_round_trips_bytes(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path)
    content = pdf_bytes()

    stored = storage.store(BytesIO(content))

    assert len(stored.identity) == 32
    assert stored.size_bytes == len(content)
    assert [path.name for path in tmp_path.iterdir()] == [
        f"{stored.identity}.pdf"
    ]
    with storage.open(stored.identity) as document:
        assert document.read() == content


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "empty"),
        (b"x" * (MAX_PDF_BYTES + 1), "exceeds"),
    ],
)
def test_storage_rejects_unsafe_sizes_and_removes_partial_file(
    tmp_path,
    content: bytes,
    message: str,
) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(DocumentBoundaryError, match=message):
        storage.store(BytesIO(content))

    assert list(tmp_path.iterdir()) == []


def test_storage_identity_cannot_escape_root(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(DocumentBoundaryError, match="identity"):
        storage.open("../../outside.db")


def test_pypdf_inspector_accepts_readable_nonempty_pdf(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path)
    stored = storage.store(BytesIO(pdf_bytes(pages=2)))

    inspection = PypdfInspector(storage).inspect(stored.identity)

    assert inspection.page_count == 2


@pytest.mark.parametrize(
    "content",
    [
        b"this is not a PDF",
        b"%PDF-1.7\nmalformed",
        pdf_bytes(pages=0),
        pdf_bytes(password="secret"),
    ],
)
def test_pypdf_inspector_rejects_non_pdf_malformed_zero_page_and_encrypted(
    tmp_path,
    content: bytes,
) -> None:
    storage = LocalDocumentStorage(tmp_path)
    stored = storage.store(BytesIO(content))

    with pytest.raises(PdfInspectionError):
        PypdfInspector(storage).inspect(stored.identity)
