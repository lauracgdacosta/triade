"""Schemas de Etiquetas (Tags)."""

import uuid

from pydantic import Field

from app.schemas.common import ORMModel


class TagCreate(ORMModel):
    name: str = Field(min_length=1, max_length=60)
    color: str = "#a855f7"


class TagRead(ORMModel):
    id: uuid.UUID
    name: str
    color: str
