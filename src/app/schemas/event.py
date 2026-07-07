"""Schemas de Eventos/Compromissos da Agenda."""

import uuid
from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common import ORMModel


class EventCreate(ORMModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    location: str | None = None
    color: str | None = None
    recurrence_rule: str | None = None
    category_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _check_range(self) -> "EventCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at deve ser posterior a start_at")
        return self


class EventUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: str | None = None
    color: str | None = None
    recurrence_rule: str | None = None
    category_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


class EventRead(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    all_day: bool
    location: str | None
    color: str | None
    recurrence_rule: str | None
    category_id: uuid.UUID | None
    project_id: uuid.UUID | None
    has_conflict: bool = False
