"""Testes de integração da página web de Busca global."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_search_page_without_query_shows_prompt(auth_client):
    response = await auth_client.get("/search")
    assert response.status_code == 200
    assert "Digite um termo para buscar" in response.text


async def test_search_page_with_query_shows_results(auth_client):
    await auth_client.post("/api/v1/tasks", json={"title": "Relatório mensal"})

    response = await auth_client.get("/search", params={"q": "relatório"})
    assert response.status_code == 200
    assert "Relatório mensal" in response.text


async def test_search_page_no_results(auth_client):
    response = await auth_client.get("/search", params={"q": "inexistente-xyz"})
    assert response.status_code == 200
    assert "Nenhum resultado" in response.text
