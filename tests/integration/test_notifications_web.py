"""Testes de integração do painel web de Notificações (HTMX)."""

import re
from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.asyncio


def _get_csrf(response) -> str:
    marker = 'name="csrf-token" content="'
    start = response.text.index(marker) + len(marker)
    end = response.text.index('"', start)
    return response.text[start:end]


async def test_notifications_panel_empty_state(auth_client):
    response = await auth_client.get("/notifications/panel")
    assert response.status_code == 200
    assert "Nenhuma notificação." in response.text


async def test_notifications_panel_shows_badge_and_mark_read(auth_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    await auth_client.post("/tasks", data={
        "title": "Vencida via form", "priority": "none", "status_filter": "pending",
        "date_": yesterday, "csrf_token": "irrelevant",
    }, headers={"X-CSRF-Token": _get_csrf(await auth_client.get("/dashboard"))})

    panel_res = await auth_client.get("/notifications/panel")
    assert panel_res.status_code == 200
    assert "Vencida via form" in panel_res.text
    assert 'id="notif-badge" class="notif-badge"' in panel_res.text

    match = re.search(r'hx-post="/notifications/([0-9a-f-]{36})/read"', panel_res.text)
    assert match is not None
    notification_id = match.group(1)
    csrf = _get_csrf(await auth_client.get("/dashboard"))
    read_res = await auth_client.post(
        f"/notifications/{notification_id}/read", headers={"X-CSRF-Token": csrf}
    )
    assert read_res.status_code == 200
    assert 'class="notif-badge d-none"' in read_res.text


async def test_mark_all_read_via_panel(auth_client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    csrf = _get_csrf(await auth_client.get("/dashboard"))
    headers = {"X-CSRF-Token": csrf}
    await auth_client.post(
        "/tasks",
        data={"title": "A", "priority": "none", "status_filter": "pending", "date_": yesterday, "csrf_token": "x"},
        headers=headers,
    )
    await auth_client.post(
        "/tasks",
        data={"title": "B", "priority": "none", "status_filter": "pending", "date_": yesterday, "csrf_token": "x"},
        headers=headers,
    )
    await auth_client.get("/notifications/panel")

    response = await auth_client.post("/notifications/read-all", headers=headers)
    assert response.status_code == 200
    assert 'class="notif-badge d-none"' in response.text
