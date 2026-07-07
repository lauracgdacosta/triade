"""Testes de integração da API REST de Notas."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app

pytestmark = pytest.mark.asyncio


async def test_create_and_get_note(auth_client):
    create_res = await auth_client.post(
        "/api/v1/notes", json={"title": "Nota via API", "content_markdown": "**oi**"}
    )
    assert create_res.status_code == 201
    body = create_res.json()
    assert body["title"] == "Nota via API"
    assert "<strong>oi</strong>" in body["content_html"]

    get_res = await auth_client.get(f"/api/v1/notes/{body['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Nota via API"


async def test_update_note(auth_client):
    create_res = await auth_client.post("/api/v1/notes", json={"title": "Original"})
    note_id = create_res.json()["id"]

    patch_res = await auth_client.patch(f"/api/v1/notes/{note_id}", json={"title": "Atualizada"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Atualizada"


async def test_delete_note(auth_client):
    create_res = await auth_client.post("/api/v1/notes", json={"title": "Excluir"})
    note_id = create_res.json()["id"]

    delete_res = await auth_client.delete(f"/api/v1/notes/{note_id}")
    assert delete_res.status_code == 204

    get_res = await auth_client.get(f"/api/v1/notes/{note_id}")
    assert get_res.status_code == 404


async def test_note_not_found_returns_404(auth_client):
    response = await auth_client.get("/api/v1/notes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_cannot_access_other_users_note(auth_client):
    create_res = await auth_client.post("/api/v1/notes", json={"title": "Privada"})
    note_id = create_res.json()["id"]

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        response = await anon_client.get(f"/api/v1/notes/{note_id}")
    assert response.status_code == 401
