"""Persistência de Notas: listagem por usuário e busca textual."""

import uuid

from sqlalchemy import or_, select

from app.models.note import Note
from app.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    model = Note

    async def list_for_user(self, user_id: uuid.UUID, *, limit: int | None = None, offset: int = 0) -> list[Note]:
        stmt = select(Note).where(Note.user_id == user_id).order_by(Note.updated_at.desc()).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, user_id: uuid.UUID, query: str) -> list[Note]:
        like = f"%{query}%"
        stmt = (
            select(Note)
            .where(Note.user_id == user_id, or_(Note.title.ilike(like), Note.content_markdown.ilike(like)))
            .order_by(Note.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
