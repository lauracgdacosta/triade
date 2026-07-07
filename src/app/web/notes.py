"""Painel lateral de Notas (Markdown, autosave via HTMX)."""

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.note_service import NoteService
from app.templating import render

router = APIRouter(prefix="/notes", tags=["web-notes"])


async def _body_context(
    request: Request, service: NoteService, user: User, selected: Note | None
) -> dict:
    notes = await service.list(user.id)
    return {
        "request": request,
        "notes": [service.to_read(n) for n in notes],
        "selected": service.to_read(selected) if selected else None,
        "csrf_token": get_or_create_csrf_token(request),
    }


@router.get("/panel", response_class=HTMLResponse)
async def notes_panel(
    request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    service = NoteService(db)
    notes = await service.list(user.id)
    context = await _body_context(request, service, user, notes[0] if notes else None)
    return render(request, "fragments/notes_panel.html", context)


@router.get("/panel/select/{note_id}", response_class=HTMLResponse)
async def select_note(
    note_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    note = await service.get(note_id, user.id)
    context = await _body_context(request, service, user, note)
    return render(request, "fragments/notes_panel_body.html", context)


@router.post("/panel/new", response_class=HTMLResponse)
async def new_note(
    request: Request,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = NoteService(db)
    note = await service.create(user.id, NoteCreate())
    context = await _body_context(request, service, user, note)
    return render(request, "fragments/notes_panel_body.html", context)


@router.patch("/panel/{note_id}", response_class=HTMLResponse)
async def save_note(
    note_id: uuid.UUID,
    request: Request,
    title: str = Form(""),
    content_markdown: str = Form(""),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = NoteService(db)
    note = await service.get(note_id, user.id)
    if note is not None:
        note = await service.update(note, NoteUpdate(title=title or None, content_markdown=content_markdown))
    context = await _body_context(request, service, user, note)
    return render(request, "fragments/notes_panel_body.html", context)


@router.delete("/panel/{note_id}", response_class=HTMLResponse)
async def delete_note(
    note_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = NoteService(db)
    note = await service.get(note_id, user.id)
    if note is not None:
        await service.delete(note)
    notes = await service.list(user.id)
    context = await _body_context(request, service, user, notes[0] if notes else None)
    return render(request, "fragments/notes_panel_body.html", context)
