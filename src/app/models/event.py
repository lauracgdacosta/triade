"""Compromissos da Agenda (dia/semana/mês), com suporte a recorrência (RRULE)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin, naive_utc


class Event(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
    end_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(20))
    recurrence_rule: Mapped[str | None] = mapped_column(String(500))  # RFC5545 RRULE

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )

    @validates("start_at", "end_at")
    def _validate_datetime(self, _key: str, value: datetime) -> datetime:
        return naive_utc(value)
