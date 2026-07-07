"""Regra de negócio de Categorias."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def list(self, user_id: uuid.UUID) -> list[Category]:
        return await self.repo.list_for_user(user_id)

    async def get(self, category_id: uuid.UUID, user_id: uuid.UUID) -> Category | None:
        return await self.repo.get_for_user(category_id, user_id)

    async def create(self, user_id: uuid.UUID, data: CategoryCreate) -> Category:
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        return await self.repo.update(category, **data.model_dump(exclude_unset=True))

    async def delete(self, category: Category) -> None:
        await self.repo.delete(category)
