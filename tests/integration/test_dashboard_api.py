"""Testes de integração do endpoint do Dashboard 'Meu Dia'."""

from datetime import date

import pytest

pytestmark = pytest.mark.asyncio


async def test_my_day_endpoint(auth_client):
    today = date.today().isoformat()
    await auth_client.post("/api/v1/tasks", json={"title": "Hoje", "date": today, "planned_duration_minutes": 30})

    response = await auth_client.get("/api/v1/dashboard/my-day", params={"day": today})
    assert response.status_code == 200
    data = response.json()
    assert data["tasks_total"] == 1
    assert data["planned_minutes"] == 30


async def test_my_day_requires_auth(client):
    response = await client.get("/api/v1/dashboard/my-day")
    assert response.status_code == 401
