"""Shared SQLAlchemy metadata for the purchase_request application."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for the application's persistent entities."""
