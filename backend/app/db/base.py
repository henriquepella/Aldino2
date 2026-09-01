"""Base declarativa do SQLAlchemy + tipo JSON portável (SQLite/Postgres)."""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


def gen_uuid() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    """Base para todos os modelos ORM."""

    type_annotation_map = {dict: JSON, list: JSON}


class UUIDMixin:
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_uuid)


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
