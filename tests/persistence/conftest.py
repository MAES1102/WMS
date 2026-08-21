import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.persistence.database import Base
from app.persistence import models


WORKFLOW_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name.startswith("purchase_request_") or table.name == "purchase_requests"
)


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine, tables=WORKFLOW_TABLES)
    with Session(engine) as session:
        yield session
        session.rollback()
    Base.metadata.drop_all(engine, tables=WORKFLOW_TABLES)


@pytest.fixture()
def purchase_request_table_names() -> set[str]:
    return {table.name for table in WORKFLOW_TABLES}
