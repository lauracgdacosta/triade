"""Schemas do Cronômetro Pomodoro."""

import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import PomodoroMode, PomodoroStatus
from app.schemas.common import ORMModel


class PomodoroStartRequest(ORMModel):
    mode: PomodoroMode = PomodoroMode.CLASSIC_25_5
    work_minutes: int = Field(default=25, ge=1, le=180)
    break_minutes: int = Field(default=5, ge=1, le=60)
    cycles_planned: int = Field(default=1, ge=1, le=20)
    task_id: uuid.UUID | None = None


class PomodoroSessionRead(ORMModel):
    id: uuid.UUID
    task_id: uuid.UUID | None
    mode: PomodoroMode
    work_minutes: int
    break_minutes: int
    cycles_planned: int
    cycles_completed: int
    status: PomodoroStatus
    started_at: datetime
    ended_at: datetime | None
