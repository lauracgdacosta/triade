"""Testes de integração da API REST de Notificações."""

from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.asyncio


async def test_list_generates_and_returns_notifications(auth_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    await auth_client.post("/api/v1/tasks", json={"title": "Vencida", "date": yesterday})

    response = await auth_client.get("/api/v1/notifications")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert "Vencida" in body[0]["title"]
    assert body[0]["read"] is False


async def test_mark_read(auth_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    await auth_client.post("/api/v1/tasks", json={"title": "Vencida", "date": yesterday})
    notifications = (await auth_client.get("/api/v1/notifications")).json()
    notification_id = notifications[0]["id"]

    response = await auth_client.post(f"/api/v1/notifications/{notification_id}/read")
    assert response.status_code == 200
    assert response.json()["read"] is True


async def test_mark_all_read(auth_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    await auth_client.post("/api/v1/tasks", json={"title": "A", "date": yesterday})
    await auth_client.post("/api/v1/tasks", json={"title": "B", "date": yesterday})
    await auth_client.get("/api/v1/notifications")

    response = await auth_client.post("/api/v1/notifications/read-all")
    assert response.status_code == 204

    notifications = (await auth_client.get("/api/v1/notifications")).json()
    assert all(n["read"] for n in notifications)


async def test_mark_read_not_found(auth_client):
    response = await auth_client.post("/api/v1/notifications/00000000-0000-0000-0000-000000000000/read")
    assert response.status_code == 404
