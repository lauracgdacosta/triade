"""Testes do NoteService: CRUD e renderização Markdown -> HTML sanitizado."""

import pytest

from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.note_service import NoteService

pytestmark = pytest.mark.asyncio


async def test_create_note(db_session, test_user: User):
    service = NoteService(db_session)
    note = await service.create(test_user.id, NoteCreate(title="Ideia", content_markdown="# Olá"))
    assert note.title == "Ideia"
    assert note.content_markdown == "# Olá"


async def test_render_html_sanitizes_script_tags(db_session, test_user: User):
    service = NoteService(db_session)
    html = service.render_html("texto <script>alert(1)</script> **negrito**")
    assert "<script>" not in html
    assert "<strong>negrito</strong>" in html


async def test_update_note_partial(db_session, test_user: User):
    service = NoteService(db_session)
    note = await service.create(test_user.id, NoteCreate(title="Original"))
    updated = await service.update(note, NoteUpdate(content_markdown="novo conteúdo"))
    assert updated.title == "Original"
    assert updated.content_markdown == "novo conteúdo"


async def test_search_matches_title_and_content(db_session, test_user: User):
    service = NoteService(db_session)
    await service.create(test_user.id, NoteCreate(title="Compras", content_markdown="leite, pão"))
    await service.create(test_user.id, NoteCreate(title="Trabalho", content_markdown="reunião às 10h"))
    results = await service.search(test_user.id, "leite")
    assert len(results) == 1
    assert results[0].title == "Compras"


async def test_delete_note(db_session, test_user: User):
    service = NoteService(db_session)
    note = await service.create(test_user.id, NoteCreate(title="Descartável"))
    await service.delete(note)
    assert await service.get(note.id, test_user.id) is None
