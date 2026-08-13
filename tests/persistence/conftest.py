import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.persistence import models


V3_TABLES = tuple(
    table
    for table in Base.metadata.sorted_tables
    if table.name.startswith("invoice_") or table.name == "invoices"
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

    Base.metadata.create_all(engine, tables=V3_TABLES)
    with Session(engine) as session:
        yield session
        session.rollback()
    Base.metadata.drop_all(engine, tables=V3_TABLES)


@pytest.fixture()
def v3_table_names() -> set[str]:
    return {table.name for table in V3_TABLES}
