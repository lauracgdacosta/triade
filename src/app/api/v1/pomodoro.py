"""Endpoints JSON do Cronômetro Pomodoro."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.pomodoro import PomodoroSessionRead, PomodoroStartRequest
from app.services.pomodoro_service import PomodoroService

router = APIRouter(prefix="/pomodoro", tags=["pomodoro"])


@router.get("/active", response_model=PomodoroSessionRead | None)
async def get_active(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    return await PomodoroService(db).get_active(user.id)


@router.post("/start", response_model=PomodoroSessionRead, status_code=status.HTTP_201_CREATED)
async def start(
    payload: PomodoroStartRequest, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    return await PomodoroService(db).start(user.id, payload)


@router.post("/{session_id}/complete-cycle", response_model=PomodoroSessionRead)
async def complete_cycle(
    session_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = PomodoroService(db)
    session = await service.get(session_id, user.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sessão não encontrada.")
    return await service.complete_cycle(session)


@router.post("/{session_id}/cancel", response_model=PomodoroSessionRead)
async def cancel(
    session_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = PomodoroService(db)
    session = await service.get(session_id, user.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sessão não encontrada.")
    return await service.cancel(session)
