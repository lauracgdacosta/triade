"""Sessões de cronômetro estilo Pomodoro."""

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin, naive_utc
from app.models.enums import PomodoroMode, PomodoroStatus


class PomodoroSession(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "pomodoro_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )
    mode: Mapped[PomodoroMode] = mapped_column(
        Enum(PomodoroMode, native_enum=False, length=20), default=PomodoroMode.CLASSIC_25_5
    )
    work_minutes: Mapped[int] = mapped_column(Integer, default=25)
    break_minutes: Mapped[int] = mapped_column(Integer, default=5)
    cycles_planned: Mapped[int] = mapped_column(Integer, default=1)
    cycles_completed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PomodoroStatus] = mapped_column(
        Enum(PomodoroStatus, native_enum=False, length=20), default=PomodoroStatus.RUNNING
    )
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column()

    @validates("started_at", "ended_at")
    def _validate_datetime(self, _key: str, value: datetime | None) -> datetime | None:
        return naive_utc(value)
