"""Schemas de perfil do usuário e preferências (Settings)."""

import uuid

from pydantic import Field

from app.models.enums import ThemeMode
from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    timezone: str
    locale: str


class UserUpdate(ORMModel):
    display_name: str | None = Field(default=None, max_length=150)
    avatar_url: str | None = Field(default=None, max_length=500)
    timezone: str | None = None
    locale: str | None = None


class SettingsRead(ORMModel):
    theme: ThemeMode
    language: str
    time_format_24h: bool
    week_start_monday: bool
    default_task_duration_minutes: int
    pomodoro_work_minutes: int
    pomodoro_break_minutes: int


class SettingsUpdate(ORMModel):
    theme: ThemeMode | None = None
    language: str | None = None
    time_format_24h: bool | None = None
    week_start_monday: bool | None = None
    default_task_duration_minutes: int | None = Field(default=None, ge=1, le=600)
    pomodoro_work_minutes: int | None = Field(default=None, ge=1, le=180)
    pomodoro_break_minutes: int | None = Field(default=None, ge=1, le=60)
