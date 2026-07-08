"""Schemas de Tarefas."""

import datetime as dt
import uuid

from pydantic import Field

from app.models.enums import Priority, TaskStatus
from app.schemas.attachment import AttachmentRead
from app.schemas.common import ORMModel
from app.schemas.tag import TagRead

# nomes dos campos ("date"/"time") coincidem com os tipos do módulo `datetime`;
# importar o módulo com alias evita que a resolução de anotações (Python 3.14
# PEP 649 / lazy annotations) confunda o nome do campo com o tipo importado.


class TaskCreate(ORMModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    notes: str | None = None
    date: dt.date | None = None
    time: dt.time | None = None
    planned_duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    priority: Priority = Priority.NONE
    category_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    color: str | None = None
    location: str | None = Field(default=None, max_length=255)
    is_recurring: bool = False
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class TaskUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    notes: str | None = None
    date: dt.date | None = None
    time: dt.time | None = None
    planned_duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    actual_duration_minutes: int | None = Field(default=None, ge=0)
    priority: Priority | None = None
    status: TaskStatus | None = None
    category_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    color: str | None = None
    location: str | None = Field(default=None, max_length=255)
    is_recurring: bool | None = None
    tag_ids: list[uuid.UUID] | None = None


class KanbanMoveRequest(ORMModel):
    kanban_column_id: uuid.UUID
    position: int = Field(ge=0)


class TaskRead(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    notes: str | None
    date: dt.date | None
    time: dt.time | None
    planned_duration_minutes: int | None
    actual_duration_minutes: int
    priority: Priority
    status: TaskStatus
    category_id: uuid.UUID | None
    project_id: uuid.UUID | None
    goal_id: uuid.UUID | None
    role_id: uuid.UUID | None
    kanban_column_id: uuid.UUID | None
    kanban_position: int
    color: str | None
    location: str | None
    completed_at: dt.datetime | None
    is_recurring: bool
    recurring_parent_id: uuid.UUID | None
    tags: list[TagRead] = Field(default_factory=list)
    attachments: list[AttachmentRead] = Field(default_factory=list)
