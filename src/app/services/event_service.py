"""Regra de negócio de Eventos/Compromissos: CRUD + detecção de conflito de horário."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import naive_utc
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventUpdate
from app.services.task_service import TaskService


class RecurrenceGoogleConflictError(ValueError):
    """Compromissos recorrentes (RRULE) não podem estar vinculados a uma conta Google."""


def _assert_recurrence_google_compatible(recurrence_rule: str | None, google_account_id) -> None:
    if recurrence_rule and google_account_id:
        raise RecurrenceGoogleConflictError(
            "Compromissos recorrentes não podem ser sincronizados com o Google Calendar."
        )


class EventService:
    def __init__(self, db: AsyncSession):
        self.repo = EventRepository(db)
        self.tasks = TaskService(db)

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
        _assert_recurrence_google_compatible(data.recurrence_rule, data.google_account_id)
        conflict = await self.has_conflict(user_id, data.start_at, data.end_at)
        event = await self.repo.create(user_id=user_id, **data.model_dump())
        await self.tasks.sync_from_event(event)
        return event, conflict

    async def update(self, event: Event, data: EventUpdate) -> tuple[Event, bool]:
        payload = data.model_dump(exclude_unset=True)
        recurrence_rule = payload.get("recurrence_rule", event.recurrence_rule)
        google_account_id = payload.get("google_account_id", event.google_account_id)
        _assert_recurrence_google_compatible(recurrence_rule, google_account_id)
        start = payload.get("start_at", event.start_at)
        end = payload.get("end_at", event.end_at)
        conflict = await self.has_conflict(event.user_id, start, end, exclude_id=event.id)
        event = await self.repo.update(event, **payload)
        await self.tasks.sync_from_event(event)
        return event, conflict

    async def delete(self, event: Event) -> None:
        await self.repo.delete(event)
