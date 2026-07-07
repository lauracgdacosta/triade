"""Persistência de Eventos/Compromissos da Agenda."""

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select

from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    async def search(self, user_id: uuid.UUID, query: str) -> list[Event]:
        like = f"%{query}%"
        stmt = select(Event).where(
            Event.user_id == user_id,
            or_(Event.title.ilike(like), Event.description.ilike(like), Event.location.ilike(like)),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.user_id == user_id, Event.start_at < end, Event.end_at > start)
            .order_by(Event.start_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_conflicts(
        self, user_id: uuid.UUID, start: datetime, end: datetime, exclude_id: uuid.UUID | None = None
    ) -> list[Event]:
        conditions = [Event.user_id == user_id, Event.start_at < end, Event.end_at > start]
        if exclude_id is not None:
            conditions.append(Event.id != exclude_id)
        stmt = select(Event).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
