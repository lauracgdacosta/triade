"""Endpoints JSON de perfil e preferências do usuário autenticado."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import SettingsRead, SettingsUpdate, UserRead, UserUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserRead)
async def get_profile(user: User = Depends(get_current_user_api)):
    return user


@router.patch("", response_model=UserRead)
async def update_profile(
    payload: UserUpdate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    return await repo.update_profile(user, **payload.model_dump(exclude_unset=True))


@router.get("/settings", response_model=SettingsRead)
async def get_settings_(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    settings = await SettingsService(db).get(user.id)
    if settings is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Preferências não encontradas.")
    return settings


@router.patch("/settings", response_model=SettingsRead)
async def update_settings(
    payload: SettingsUpdate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = SettingsService(db)
    settings = await service.get(user.id)
    if settings is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Preferências não encontradas.")
    return await service.update(settings, payload)
