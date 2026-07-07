"""Persistência de Projetos."""

import uuid

from sqlalchemy import or_, select

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def search(self, user_id: uuid.UUID, query: str) -> list[Project]:
        like = f"%{query}%"
        stmt = select(Project).where(
            Project.user_id == user_id, or_(Project.name.ilike(like), Project.description.ilike(like))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
