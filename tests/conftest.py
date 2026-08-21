"""Isolated integration fixtures for the final application."""

import os
os.environ.setdefault("WORKFLOW_DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.persistence.bootstrap import WORKFLOW_TABLES
from app.persistence.database import Base
from app.runtime import purchase_request_engine, purchase_request_event_bus


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=purchase_request_engine, tables=WORKFLOW_TABLES)
    with TestClient(app) as value:
        yield value
    Base.metadata.drop_all(bind=purchase_request_engine, tables=WORKFLOW_TABLES)
    assert purchase_request_event_bus.subscriber_count == 0
