"""Regra de negócio de Etiquetas (Tags)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreate


class TagService:
    def __init__(self, db: AsyncSession):
        self.repo = TagRepository(db)

    async def list(self, user_id: uuid.UUID) -> list[Tag]:
        return await self.repo.list_for_user(user_id)

    async def get_or_create_many(self, user_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> list[Tag]:
        tags = []
        for tag_id in tag_ids:
            tag = await self.repo.get_for_user(tag_id, user_id)
            if tag:
                tags.append(tag)
        return tags

    async def create(self, user_id: uuid.UUID, data: TagCreate) -> Tag:
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def delete(self, tag: Tag) -> None:
        await self.repo.delete(tag)
