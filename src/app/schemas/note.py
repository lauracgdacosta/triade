"""Schemas de Notas."""

import datetime as dt
import uuid

from pydantic import Field

from app.schemas.common import ORMModel


class NoteCreate(ORMModel):
    title: str | None = Field(default=None, max_length=255)
    content_markdown: str = ""


class NoteUpdate(ORMModel):
    title: str | None = Field(default=None, max_length=255)
    content_markdown: str | None = None


class NoteRead(ORMModel):
    id: uuid.UUID
    title: str | None
    content_markdown: str
    content_html: str
    updated_at: dt.datetime
