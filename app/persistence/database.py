"""Shared SQLAlchemy metadata for the invoice application."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for the application's persistent entities."""
