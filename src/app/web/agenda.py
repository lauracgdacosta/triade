"""Página da Agenda (visões dia/semana/mês) — dados carregados via API JSON (FullCalendar)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.services.category_service import CategoryService
from app.services.event_service import EventService
from app.services.google_calendar_account_service import GoogleCalendarAccountService
from app.services.google_calendar_sync_service import GoogleCalendarSyncService
from app.services.project_service import ProjectService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/agenda", tags=["web-agenda"])


def _form_values(event: Event | None, prefill_start: str, prefill_end: str) -> dict:
    if event is None:
        return {
            "id": "",
            "title": "",
            "description": "",
            "start_at": prefill_start,
            "end_at": prefill_end,
            "category_id": "",
            "project_id": "",
            "location": "",
            "color": "#6366f1",
            "recurrence_rule": "",
            "google_account_id": "",
        }
    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description or "",
        "start_at": event.start_at.isoformat(),
        "end_at": event.end_at.isoformat(),
        "category_id": str(event.category_id) if event.category_id else "",
        "project_id": str(event.project_id) if event.project_id else "",
        "location": event.location or "",
        "color": event.color or "#6366f1",
        "recurrence_rule": event.recurrence_rule or "",
        "google_account_id": str(event.google_account_id) if event.google_account_id else "",
    }


@router.get("", response_class=HTMLResponse)
async def agenda_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    # Pull lazy: só roda quando a Agenda é aberta (sem worker/cron neste
    # deploy serverless). Nunca deixa uma falha do Google derrubar a
    # página — GoogleCalendarSyncService.pull_all_accounts já trata isso.
    await GoogleCalendarSyncService(db).pull_all_accounts(user.id)
    context = await base_context(request, user, db)
    context["categories"] = await CategoryService(db).list(user.id)
    context["projects"] = await ProjectService(db).list(user.id)
    return render(request, "pages/agenda.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_event_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    context = await base_context(request, user, db)
    context["categories"] = await CategoryService(db).list(user.id)
    context["projects"] = await ProjectService(db).list(user.id)
    context["google_accounts"] = await GoogleCalendarAccountService(db).list_active(user.id)
    context["is_edit"] = False
    context["form_values"] = _form_values(None, start or "", end or "")
    return render(request, "pages/event_form.html", context)


@router.get("/{event_id}/edit", response_class=HTMLResponse)
async def edit_event_page(
    request: Request,
    event_id: uuid.UUID,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    event = await EventService(db).get(event_id, user.id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Compromisso não encontrado.")
    context = await base_context(request, user, db)
    context["categories"] = await CategoryService(db).list(user.id)
    context["projects"] = await ProjectService(db).list(user.id)
    context["google_accounts"] = await GoogleCalendarAccountService(db).list_active(user.id)
    context["is_edit"] = True
    context["form_values"] = _form_values(event, "", "")
    return render(request, "pages/event_form.html", context)
