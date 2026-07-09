"""Endpoints JSON de Eventos/Compromissos da Agenda."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.event_service import EventService, RecurrenceGoogleConflictError
from app.services.google_calendar_sync_service import GoogleCalendarSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


async def _push_to_google(db: AsyncSession, action: str, event: Event) -> Event:
    """Push best-effort: o evento já foi persistido localmente antes desta
    chamada — uma falha aqui (rede, token revogado) não deve derrubar a
    resposta da API, só deixar `google_event_id` desatualizado até a
    próxima tentativa."""
    try:
        sync = GoogleCalendarSyncService(db)
        if action == "create":
            return await sync.push_create(event)
        if action == "update":
            return await sync.push_update(event)
        await sync.push_delete(event)
        return event
    except Exception:
        logger.exception("Falha ao sincronizar evento %s com o Google (%s)", event.id, action)
        return event


def _to_read(event, conflict: bool = False) -> EventRead:
    data = EventRead.model_validate(event).model_dump()
    data["has_conflict"] = conflict
    return EventRead(**data)


@router.get("", response_model=list[EventRead])
async def list_events(
    start: datetime,
    end: datetime,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    events = await EventService(db).list_in_range(user.id, start, end)
    return [_to_read(e) for e in events]


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    try:
        event, conflict = await EventService(db).create(user.id, payload)
    except RecurrenceGoogleConflictError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    event = await _push_to_google(db, "create", event)
    return _to_read(event, conflict)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    event = await EventService(db).get(event_id, user.id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compromisso não encontrado.")
    return _to_read(event)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = EventService(db)
    event = await service.get(event_id, user.id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compromisso não encontrado.")
    try:
        event, conflict = await service.update(event, payload)
    except RecurrenceGoogleConflictError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    event = await _push_to_google(db, "update", event)
    return _to_read(event, conflict)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = EventService(db)
    event = await service.get(event_id, user.id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compromisso não encontrado.")
    await _push_to_google(db, "delete", event)
    await service.delete(event)
