"""Regra de negócio de Papéis (Roles)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, db: AsyncSession):
        self.repo = RoleRepository(db)

    async def list(self, user_id: uuid.UUID) -> list[Role]:
        return await self.repo.list_for_user(user_id)

    async def get(self, role_id: uuid.UUID, user_id: uuid.UUID) -> Role | None:
        return await self.repo.get_for_user(role_id, user_id)

    async def create(self, user_id: uuid.UUID, data: RoleCreate) -> Role:
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def update(self, role: Role, data: RoleUpdate) -> Role:
        return await self.repo.update(role, **data.model_dump(exclude_unset=True))

    async def delete(self, role: Role) -> None:
        await self.repo.delete(role)
