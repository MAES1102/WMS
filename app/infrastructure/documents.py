"""Controlled local document storage with generated identities."""

from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.application.document_ports import (
    DocumentStorageBoundaryError,
    StoredDocument,
)
from app.application.invoice_validation import MAX_PDF_BYTES


_CHUNK_SIZE = 64 * 1024


class DocumentBoundaryError(DocumentStorageBoundaryError):
    pass


class LocalDocumentStorage:
    """Store bytes under generated names; caller filenames are never accepted."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def store(self, source: BinaryIO) -> StoredDocument:
        identity = uuid4().hex
        target = self._path_for(identity)
        total = 0
        try:
            with target.open("xb") as output:
                while True:
                    chunk = source.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_PDF_BYTES:
                        raise DocumentBoundaryError(
                            "document exceeds the 10 MiB limit"
                        )
                    output.write(chunk)
            if total == 0:
                raise DocumentBoundaryError("document is empty")
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        return StoredDocument(identity=identity, size_bytes=total)

    def open(self, identity: str) -> BinaryIO:
        return self._path_for(identity).open("rb")

    def delete(self, identity: str) -> None:
        self._path_for(identity).unlink(missing_ok=True)

    def _path_for(self, identity: str) -> Path:
        if len(identity) != 32 or any(
            character not in "0123456789abcdef" for character in identity
        ):
            raise DocumentBoundaryError("invalid document identity")
        return self._root / f"{identity}.pdf"
