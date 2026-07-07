"""Schemas de Papéis (Roles)."""

import uuid

from pydantic import Field

from app.schemas.common import ORMModel


class RoleCreate(ORMModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = "#6366f1"
    icon: str = "fa-solid fa-briefcase"


class RoleUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None
    icon: str | None = None


class RoleRead(ORMModel):
    id: uuid.UUID
    name: str
    color: str
    icon: str
