"""Testes de integração: push Tríade -> Google Calendar disparado pela API de eventos."""

import httpx
import pytest
import respx

from app.models.user import User
from app.services.google_calendar_account_service import GoogleCalendarAccountService

pytestmark = pytest.mark.asyncio

_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


@pytest.fixture
async def google_account_id(db_session, test_user: User) -> str:
    account = await GoogleCalendarAccountService(db_session).create_from_oauth(
        test_user.id,
        google_sub="sub-1",
        email="trabalho@example.com",
        access_token="at-1",
        refresh_token="rt-1",
        expires_in=3600,
        scope="https://www.googleapis.com/auth/calendar",
    )
    await db_session.commit()
    return str(account.id)


@respx.mock
async def test_create_event_with_google_account_pushes_to_google(auth_client, google_account_id):
    respx.post(_EVENTS_URL).mock(return_value=httpx.Response(200, json={"id": "gcal-novo"}))

    response = await auth_client.post(
        "/api/v1/events",
        json={
            "title": "Reunião de trabalho",
            "start_at": "2026-05-01T09:00:00",
            "end_at": "2026-05-01T10:00:00",
            "google_account_id": google_account_id,
        },
    )
    assert response.status_code == 201
    assert response.json()["google_event_id"] == "gcal-novo"


@respx.mock
async def test_update_event_with_google_account_pushes_update(auth_client, google_account_id):
    respx.post(_EVENTS_URL).mock(return_value=httpx.Response(200, json={"id": "gcal-1"}))
    create_res = await auth_client.post(
        "/api/v1/events",
        json={
            "title": "Original",
            "start_at": "2026-05-01T09:00:00",
            "end_at": "2026-05-01T10:00:00",
            "google_account_id": google_account_id,
        },
    )
    event_id = create_res.json()["id"]

    update_route = respx.patch(f"{_EVENTS_URL}/gcal-1").mock(
        return_value=httpx.Response(200, json={"id": "gcal-1", "summary": "Atualizado"})
    )
    update_res = await auth_client.patch(f"/api/v1/events/{event_id}", json={"title": "Atualizado"})
    assert update_res.status_code == 200
    assert update_route.called


@respx.mock
async def test_delete_event_with_google_account_pushes_delete(auth_client, google_account_id):
    respx.post(_EVENTS_URL).mock(return_value=httpx.Response(200, json={"id": "gcal-1"}))
    create_res = await auth_client.post(
        "/api/v1/events",
        json={
            "title": "Excluir",
            "start_at": "2026-05-01T09:00:00",
            "end_at": "2026-05-01T10:00:00",
            "google_account_id": google_account_id,
        },
    )
    event_id = create_res.json()["id"]

    delete_route = respx.delete(f"{_EVENTS_URL}/gcal-1").mock(return_value=httpx.Response(204))
    delete_res = await auth_client.delete(f"/api/v1/events/{event_id}")
    assert delete_res.status_code == 204
    assert delete_route.called


async def test_recurring_event_with_google_account_is_rejected(auth_client, google_account_id):
    response = await auth_client.post(
        "/api/v1/events",
        json={
            "title": "Recorrente",
            "start_at": "2026-05-01T09:00:00",
            "end_at": "2026-05-01T10:00:00",
            "recurrence_rule": "FREQ=WEEKLY",
            "google_account_id": google_account_id,
        },
    )
    assert response.status_code == 422


async def test_google_push_failure_does_not_break_create_response(auth_client, google_account_id):
    # insert_event falhando (500) não deve derrubar a resposta da API — o
    # evento já foi salvo localmente antes do push ser tentado.
    with respx.mock:
        respx.post(_EVENTS_URL).mock(return_value=httpx.Response(500, json={"error": {"message": "boom"}}))
        response = await auth_client.post(
            "/api/v1/events",
            json={
                "title": "Falha simulada no Google",
                "start_at": "2026-05-01T09:00:00",
                "end_at": "2026-05-01T10:00:00",
                "google_account_id": google_account_id,
            },
        )
    assert response.status_code == 201
    assert response.json()["google_event_id"] is None
