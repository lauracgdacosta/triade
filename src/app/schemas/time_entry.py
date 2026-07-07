"""Schemas de registros manuais de tempo."""

import uuid
from datetime import datetime

from pydantic import model_validator

from app.schemas.common import ORMModel


class TimeEntryCreate(ORMModel):
    task_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def _check_range(self) -> "TimeEntryCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at deve ser posterior a start_at")
        return self


class TimeEntryRead(ORMModel):
    id: uuid.UUID
    task_id: uuid.UUID | None
    project_id: uuid.UUID | None
    category_id: uuid.UUID | None
    role_id: uuid.UUID | None
    start_at: datetime
    end_at: datetime | None
    duration_minutes: int
