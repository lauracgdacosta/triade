"""Preferências do usuário: tema, pomodoro padrão, formato de hora, etc."""

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ThemeMode


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    theme: Mapped[ThemeMode] = mapped_column(
        Enum(ThemeMode, native_enum=False, length=10), default=ThemeMode.AUTO
    )
    language: Mapped[str] = mapped_column(String(10), default="pt-BR")
    time_format_24h: Mapped[bool] = mapped_column(Boolean, default=True)
    week_start_monday: Mapped[bool] = mapped_column(Boolean, default=True)
    default_task_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    pomodoro_work_minutes: Mapped[int] = mapped_column(Integer, default=25)
    pomodoro_break_minutes: Mapped[int] = mapped_column(Integer, default=5)

    user: Mapped["User"] = relationship(back_populates="settings")  # noqa: F821
