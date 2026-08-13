"""pypdf adapter for bounded structural inspection."""

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.application.invoice_validation import PdfInspection, PdfInspectionError
from app.infrastructure.documents import LocalDocumentStorage


class PypdfInspector:
    def __init__(self, storage: LocalDocumentStorage) -> None:
        self._storage = storage

    def inspect(self, document_identity: str) -> PdfInspection:
        try:
            with self._storage.open(document_identity) as document:
                reader = PdfReader(document, strict=True)
                if reader.is_encrypted:
                    raise PdfInspectionError("encrypted PDF is not accepted")
                page_count = len(reader.pages)
        except PdfInspectionError:
            raise
        except (PdfReadError, EOFError, OSError, ValueError) as exc:
            raise PdfInspectionError("PDF is malformed or unreadable") from exc
        if page_count < 1:
            raise PdfInspectionError("PDF must contain at least one page")
        return PdfInspection(page_count=page_count)
