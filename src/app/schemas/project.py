"""Schemas de Projetos."""

import uuid
from datetime import date

from pydantic import Field

from app.schemas.common import ORMModel


class ProjectCreate(ORMModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    color: str = "#22c55e"
    deadline: date | None = None


class ProjectUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    color: str | None = None
    deadline: date | None = None
    percent_complete: float | None = Field(default=None, ge=0, le=100)


class ProjectRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    color: str
    deadline: date | None
    percent_complete: float
