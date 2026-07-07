"""Endpoints JSON de Notificações: listar, marcar lida(s)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = NotificationService(db)
    await service.generate_pending(user.id)
    return await service.list(user.id)


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notification = await service.get(notification_id, user.id)
    if notification is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificação não encontrada.")
    return await service.mark_read(notification)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    await NotificationService(db).mark_all_read(user.id)
