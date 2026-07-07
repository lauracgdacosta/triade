"""Endpoints JSON de Notas: CRUD."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate
from app.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


async def _get_owned_note(note_id: uuid.UUID, user: User, service: NoteService):
    note = await service.get(note_id, user.id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nota não encontrada.")
    return note


@router.get("", response_model=list[NoteRead])
async def list_notes(
    q: str | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    notes = await service.search(user.id, q) if q else await service.list(user.id)
    return [service.to_read(note) for note in notes]


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = NoteService(db)
    note = await service.create(user.id, payload)
    return service.to_read(note)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = NoteService(db)
    note = await _get_owned_note(note_id, user, service)
    return service.to_read(note)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    note = await _get_owned_note(note_id, user, service)
    note = await service.update(note, payload)
    return service.to_read(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = NoteService(db)
    note = await _get_owned_note(note_id, user, service)
    await service.delete(note)
