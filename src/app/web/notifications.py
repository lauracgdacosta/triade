"""Central de notificações no topbar (dropdown HTMX)."""

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.user import User
from app.services.notification_service import NotificationService
from app.templating import render

router = APIRouter(prefix="/notifications", tags=["web-notifications"])


async def _panel_context(request: Request, service: NotificationService, user: User) -> dict:
    notifications = await service.list(user.id)
    unread_count = await service.count_unread(user.id)
    return {"request": request, "notifications": notifications, "unread_count": unread_count}


@router.get("/panel", response_class=HTMLResponse)
async def notifications_panel(
    request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    service = NotificationService(db)
    await service.generate_pending(user.id)
    context = await _panel_context(request, service, user)
    return render(request, "fragments/notifications_panel.html", context)


@router.post("/{notification_id}/read", response_class=HTMLResponse)
async def mark_read(
    notification_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = NotificationService(db)
    notification = await service.get(notification_id, user.id)
    if notification is not None:
        await service.mark_read(notification)
    context = await _panel_context(request, service, user)
    return render(request, "fragments/notifications_panel.html", context)


@router.post("/read-all", response_class=HTMLResponse)
async def mark_all_read(
    request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    service = NotificationService(db)
    await service.mark_all_read(user.id)
    context = await _panel_context(request, service, user)
    return render(request, "fragments/notifications_panel.html", context)
