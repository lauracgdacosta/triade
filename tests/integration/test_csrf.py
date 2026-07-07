"""Testes de integração da proteção CSRF (double-submit cookie) nas rotas web."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_post_without_csrf_token_is_rejected(auth_client):
    # sem visitar nenhuma página antes, o cliente não tem cookie de CSRF
    response = await auth_client.post(
        "/categories",
        data={"name": "Sem token", "icon": "fa-solid fa-tag", "color": "#000000", "csrf_token": "forjado"},
    )
    assert response.status_code == 403


async def test_post_with_valid_csrf_token_succeeds(auth_client):
    page = await auth_client.get("/categories")
    marker = 'name="csrf-token" content="'
    start = page.text.index(marker) + len(marker)
    token = page.text[start : page.text.index('"', start)]

    response = await auth_client.post(
        "/categories",
        data={"name": "Com token", "icon": "fa-solid fa-tag", "color": "#000000", "csrf_token": token},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
    assert "Com token" in response.text
