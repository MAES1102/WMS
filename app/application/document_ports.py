"""Application-owned contracts for controlled document storage."""

from dataclasses import dataclass
from typing import BinaryIO, Protocol


class DocumentStorageBoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class StoredDocument:
    identity: str
    size_bytes: int


class DocumentStorage(Protocol):
    def store(self, source: BinaryIO) -> StoredDocument:
        """Store a bounded stream under a generated identity."""

    def delete(self, identity: str) -> None:
        """Delete a document during compensation or retention cleanup."""
