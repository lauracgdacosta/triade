"""Repository genérico (Repository Pattern) com operações CRUD comuns."""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id_: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def get_for_user(self, id_: uuid.UUID, user_id: uuid.UUID) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == id_, self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: uuid.UUID, *, limit: int | None = None, offset: int = 0
    ) -> list[ModelT]:
        stmt = select(self.model).where(self.model.user_id == user_id).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs: object) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **kwargs: object) -> ModelT:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def delete_by_id_for_user(self, id_: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = delete(self.model).where(self.model.id == id_, self.model.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.flush()
