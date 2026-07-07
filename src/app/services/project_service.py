"""Regra de negócio de Projetos."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def list(self, user_id: uuid.UUID) -> list[Project]:
        return await self.repo.list_for_user(user_id)

    async def get(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project | None:
        return await self.repo.get_for_user(project_id, user_id)

    async def create(self, user_id: uuid.UUID, data: ProjectCreate) -> Project:
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def update(self, project: Project, data: ProjectUpdate) -> Project:
        return await self.repo.update(project, **data.model_dump(exclude_unset=True))

    async def delete(self, project: Project) -> None:
        await self.repo.delete(project)
