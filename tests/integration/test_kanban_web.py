"""Testes de integração da página web do Kanban (inclui hooks do Supabase Realtime)."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_kanban_page_renders_realtime_data_attributes(auth_client):
    response = await auth_client.get("/kanban")
    assert response.status_code == 200
    assert 'id="kanban-board"' in response.text
    assert "data-supabase-url=" in response.text
    assert "data-supabase-anon-key=" in response.text
    assert "data-user-id=" in response.text


async def test_kanban_page_loads_supabase_js_cdn(auth_client):
    response = await auth_client.get("/kanban")
    assert "@supabase/supabase-js" in response.text
