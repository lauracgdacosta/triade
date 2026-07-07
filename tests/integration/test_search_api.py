"""Testes de integração da API JSON de Busca global."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_search_across_entities(auth_client):
    await auth_client.post("/api/v1/tasks", json={"title": "Planejar viagem"})
    await auth_client.post("/api/v1/projects", json={"name": "Viagem 2026"})

    response = await auth_client.get("/api/v1/search", params={"q": "viagem"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["query"] == "viagem"


async def test_search_requires_auth(client):
    response = await client.get("/api/v1/search", params={"q": "x"})
    assert response.status_code == 401
