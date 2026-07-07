"""Schemas de Busca global."""

import uuid

from pydantic import Field

from app.schemas.common import ORMModel


class SearchResult(ORMModel):
    entity_type: str
    id: uuid.UUID
    title: str
    subtitle: str | None = None
    url: str


class SearchResponse(ORMModel):
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0
