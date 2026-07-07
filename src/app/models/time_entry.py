"""Registros de tempo gasto (manual ou via Pomodoro), base dos relatórios."""

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin, naive_utc
from app.models.enums import TimeEntrySource


class TimeEntry(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "time_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), index=True
    )

    start_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
    end_at: Mapped[datetime | None] = mapped_column()
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[TimeEntrySource] = mapped_column(
        Enum(TimeEntrySource, native_enum=False, length=20), default=TimeEntrySource.MANUAL
    )

    @validates("start_at", "end_at")
    def _validate_datetime(self, _key: str, value: datetime | None) -> datetime | None:
        return naive_utc(value)
