"""Regra de negócio de Notas: CRUD + renderização segura do Markdown para HTML."""

from __future__ import annotations

import uuid

import markdown as markdown_lib
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.repositories.note_repository import NoteRepository
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate
from app.utils.sanitize import sanitize_html


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NoteRepository(db)

    def render_html(self, content_markdown: str) -> str:
        raw_html = markdown_lib.markdown(content_markdown, extensions=["fenced_code", "tables"])
        return sanitize_html(raw_html) or ""

    def to_read(self, note: Note) -> NoteRead:
        return NoteRead(
            id=note.id,
            title=note.title,
            content_markdown=note.content_markdown,
            content_html=self.render_html(note.content_markdown),
            updated_at=note.updated_at,
        )

    async def list(self, user_id: uuid.UUID) -> list[Note]:
        return await self.repo.list_for_user(user_id)

    async def search(self, user_id: uuid.UUID, query: str) -> list[Note]:
        return await self.repo.search(user_id, query)

    async def get(self, note_id: uuid.UUID, user_id: uuid.UUID) -> Note | None:
        return await self.repo.get_for_user(note_id, user_id)

    async def create(self, user_id: uuid.UUID, data: NoteCreate) -> Note:
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def update(self, note: Note, data: NoteUpdate) -> Note:
        payload = data.model_dump(exclude_unset=True)
        return await self.repo.update(note, **payload)

    async def delete(self, note: Note) -> None:
        await self.repo.delete(note)
