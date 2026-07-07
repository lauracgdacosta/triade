"""Persistência de Notificações: listagem, contagem de não lidas e dedupe diário."""

import uuid
from datetime import datetime

from sqlalchemy import func, select, update

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    async def list_for_user(
        self, user_id: uuid.UUID, *, limit: int | None = None, offset: int = 0
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.read.is_(False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_since(
        self, user_id: uuid.UUID, type_: NotificationType, title: str, since: datetime
    ) -> bool:
        stmt = (
            select(Notification.id)
            .where(
                Notification.user_id == user_id,
                Notification.type == type_,
                Notification.title == title,
                Notification.created_at >= since,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read.is_(False))
            .values(read=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()
