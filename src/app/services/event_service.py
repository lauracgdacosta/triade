"""Regra de negócio de Eventos/Compromissos: CRUD + detecção de conflito de horário."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import naive_utc
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventUpdate


class EventService:
    def __init__(self, db: AsyncSession):
        self.repo = EventRepository(db)

    async def list_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[Event]:
        # `start`/`end` chegam timezone-aware do FullCalendar (ISO 8601 com
        # offset); Event.start_at/end_at não são timezone-aware no Postgres —
        # ver app.models.base.naive_utc. Sem isso, o fetch de eventos da
        # Agenda quebra com "can't subtract offset-naive and offset-aware
        # datetimes" (só reproduz contra Postgres real, não SQLite).
        return await self.repo.list_in_range(user_id, naive_utc(start), naive_utc(end))

    async def get(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Event | None:
        return await self.repo.get_for_user(event_id, user_id)

    async def has_conflict(
        self, user_id: uuid.UUID, start: datetime, end: datetime, exclude_id: uuid.UUID | None = None
    ) -> bool:
        conflicts = await self.repo.find_conflicts(user_id, naive_utc(start), naive_utc(end), exclude_id)
        return len(conflicts) > 0

    async def create(self, user_id: uuid.UUID, data: EventCreate) -> tuple[Event, bool]:
        conflict = await self.has_conflict(user_id, data.start_at, data.end_at)
        event = await self.repo.create(user_id=user_id, **data.model_dump())
        return event, conflict

    async def update(self, event: Event, data: EventUpdate) -> tuple[Event, bool]:
        payload = data.model_dump(exclude_unset=True)
        start = payload.get("start_at", event.start_at)
        end = payload.get("end_at", event.end_at)
        conflict = await self.has_conflict(event.user_id, start, end, exclude_id=event.id)
        event = await self.repo.update(event, **payload)
        return event, conflict

    async def delete(self, event: Event) -> None:
        await self.repo.delete(event)
