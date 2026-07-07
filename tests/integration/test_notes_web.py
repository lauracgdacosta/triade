"""Testes de integração do painel web de Notas (HTMX)."""

import pytest

pytestmark = pytest.mark.asyncio


def _get_csrf(response) -> str:
    marker = 'name="csrf-token" content="'
    start = response.text.index(marker) + len(marker)
    end = response.text.index('"', start)
    return response.text[start:end]


async def test_notes_panel_empty_state(auth_client):
    response = await auth_client.get("/notes/panel")
    assert response.status_code == 200
    assert "Nenhuma nota ainda." in response.text


async def test_create_note_via_panel_and_autosave(auth_client):
    csrf = _get_csrf(await auth_client.get("/dashboard"))
    headers = {"X-CSRF-Token": csrf}

    create_res = await auth_client.post("/notes/panel/new", headers=headers)
    assert create_res.status_code == 200
    assert 'name="content_markdown"' in create_res.text

    note_id = create_res.text.split('hx-patch="/notes/panel/')[1].split('"')[0]

    save_res = await auth_client.patch(
        f"/notes/panel/{note_id}",
        data={"title": "Minha nota", "content_markdown": "conteúdo salvo", "csrf_token": csrf},
        headers=headers,
    )
    assert save_res.status_code == 200
    assert "Minha nota" in save_res.text
    assert "conteúdo salvo" in save_res.text


async def test_delete_note_via_panel(auth_client):
    csrf = _get_csrf(await auth_client.get("/dashboard"))
    headers = {"X-CSRF-Token": csrf}

    create_res = await auth_client.post("/notes/panel/new", headers=headers)
    note_id = create_res.text.split('hx-patch="/notes/panel/')[1].split('"')[0]

    delete_res = await auth_client.delete(f"/notes/panel/{note_id}", headers=headers)
    assert delete_res.status_code == 200
    assert "Nenhuma nota ainda." in delete_res.text
