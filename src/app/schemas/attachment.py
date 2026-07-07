"""Schemas de anexos de tarefas."""

import uuid

from app.schemas.common import ORMModel


class AttachmentRead(ORMModel):
    id: uuid.UUID
    file_name: str
    file_url: str
    mime_type: str | None
    size_bytes: int | None
