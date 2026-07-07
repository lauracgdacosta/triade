"""Schemas de Metas."""

import uuid
from datetime import date

from pydantic import Field

from app.schemas.common import ORMModel


class GoalCreate(ORMModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = None
    project_id: uuid.UUID | None = None
    deadline: date | None = None


class GoalUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    project_id: uuid.UUID | None = None
    deadline: date | None = None
    percent_complete: float | None = Field(default=None, ge=0, le=100)


class GoalRead(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    project_id: uuid.UUID | None
    deadline: date | None
    percent_complete: float
    tasks_done: int = 0
    tasks_total: int = 0
