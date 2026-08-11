import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# URL из ENV: легко переключить SQLite→Postgres без правки кода (12-factor)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workflow.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# SQLite по умолчанию не проверяет FK — включаем на каждом соединении
@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


# фабрика сессий для DI; autocommit=False  явный commit (контроль транзакций)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# базовый класс ORM: собирает metadata всех моделей для create_all
class Base(DeclarativeBase):
    pass
