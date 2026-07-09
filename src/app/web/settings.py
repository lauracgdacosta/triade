"""Página de Configurações: tema, idioma, formato de hora, pomodoro padrão."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.enums import ThemeMode
from app.models.user import User
from app.schemas.user import SettingsUpdate
from app.services.google_calendar_account_service import GoogleCalendarAccountService
from app.services.settings_service import SettingsService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/settings", tags=["web-settings"])


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    context["saved"] = False
    context["google_accounts"] = await GoogleCalendarAccountService(db).list(user.id)
    return render(request, "pages/settings.html", context)


@router.post("", response_class=HTMLResponse)
async def update_settings(
    request: Request,
    theme: str = Form("auto"),
    language: str = Form("pt-BR"),
    time_format_24h: bool = Form(False),
    week_start_monday: bool = Form(False),
    default_task_duration_minutes: int = Form(30),
    pomodoro_work_minutes: int = Form(25),
    pomodoro_break_minutes: int = Form(5),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = SettingsService(db)
    settings = await service.get(user.id)
    await service.update(
        settings,
        SettingsUpdate(
            theme=ThemeMode(theme),
            language=language,
            time_format_24h=time_format_24h,
            week_start_monday=week_start_monday,
            default_task_duration_minutes=default_task_duration_minutes,
            pomodoro_work_minutes=pomodoro_work_minutes,
            pomodoro_break_minutes=pomodoro_break_minutes,
        ),
    )
    context = await base_context(request, user, db)
    context["saved"] = True
    context["google_accounts"] = await GoogleCalendarAccountService(db).list(user.id)
    return render(request, "pages/settings.html", context)
