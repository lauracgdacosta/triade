"""Endpoints JSON de Eventos/Compromissos da Agenda."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


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
    event, conflict = await EventService(db).create(user.id, payload)
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
    event, conflict = await service.update(event, payload)
    return _to_read(event, conflict)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = EventService(db)
    event = await service.get(event_id, user.id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compromisso não encontrado.")
    await service.delete(event)
