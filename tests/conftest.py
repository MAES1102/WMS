"""Shared fixtures for integrated invoice-application tests."""
import os
from pathlib import Path
import shutil

os.environ.setdefault("INVOICE_DATABASE_URL", "sqlite://")
os.environ.setdefault("INVOICE_STORAGE_ROOT", "/tmp/wms-invoice-test-documents")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.persistence.bootstrap import INVOICE_TABLES
from app.persistence.database import Base
from app.runtime import invoice_engine


_STORAGE_ROOT = Path(os.environ["INVOICE_STORAGE_ROOT"])


@pytest.fixture()
def client():
    """Yield a TestClient backed by a fresh in-memory SQLite database."""
    Base.metadata.drop_all(bind=invoice_engine, tables=INVOICE_TABLES)
    shutil.rmtree(_STORAGE_ROOT, ignore_errors=True)
    _STORAGE_ROOT.mkdir(parents=True)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=invoice_engine, tables=INVOICE_TABLES)
    shutil.rmtree(_STORAGE_ROOT, ignore_errors=True)
