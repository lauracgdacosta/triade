"""Schemas de Quadros e Colunas Kanban."""

import uuid

from pydantic import Field

from app.models.enums import TaskStatus
from app.schemas.common import ORMModel
from app.schemas.task import TaskRead


class KanbanColumnCreate(ORMModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = "#64748b"


class KanbanColumnUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None
    position: int | None = None


class KanbanColumnRead(ORMModel):
    id: uuid.UUID
    name: str
    color: str
    position: int
    maps_to_status: TaskStatus | None = None
    tasks: list[TaskRead] = Field(default_factory=list)


class KanbanBoardRead(ORMModel):
    id: uuid.UUID
    name: str
    is_default: bool
    columns: list[KanbanColumnRead] = Field(default_factory=list)
