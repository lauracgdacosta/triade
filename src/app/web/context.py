"""Contexto comum (usuário, CSRF, preferências) injetado em toda página autenticada."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token
from app.models.user import User
from app.services.settings_service import SettingsService
from app.services.task_service import TaskService


async def base_context(request: Request, user: User, db: AsyncSession) -> dict:
    await TaskService(db).ensure_recurring_occurrences(user.id)
    settings = await SettingsService(db).get(user.id)
    return {
        "request": request,
        "user": user,
        "csrf_token": get_or_create_csrf_token(request),
        "user_settings": settings,
        "active_path": request.url.path,
    }
