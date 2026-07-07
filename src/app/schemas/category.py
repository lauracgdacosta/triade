"""Schemas de Categorias."""

import uuid

from pydantic import Field

from app.schemas.common import ORMModel


class CategoryCreate(ORMModel):
    name: str = Field(min_length=1, max_length=100)
    icon: str = "fa-solid fa-tag"
    color: str = "#0ea5e9"


class CategoryUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = None
    color: str | None = None


class CategoryRead(ORMModel):
    id: uuid.UUID
    name: str
    icon: str
    color: str
