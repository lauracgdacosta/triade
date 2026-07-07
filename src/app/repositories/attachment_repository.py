"""Persistência de anexos de tarefas."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_task(self, task_id: uuid.UUID) -> list[Attachment]:
        result = await self.session.execute(select(Attachment).where(Attachment.task_id == task_id))
        return list(result.scalars().all())

    async def get(self, id_: uuid.UUID) -> Attachment | None:
        return await self.session.get(Attachment, id_)

    async def create(self, **kwargs: object) -> Attachment:
        obj = Attachment(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: Attachment) -> None:
        await self.session.delete(obj)
        await self.session.flush()
