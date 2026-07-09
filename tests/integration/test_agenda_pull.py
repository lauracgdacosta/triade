"""Testes de integração: pull Google -> Tríade disparado ao abrir /agenda."""

import httpx
import pytest
import respx

from app.models.user import User
from app.services.google_calendar_account_service import GoogleCalendarAccountService

pytestmark = pytest.mark.asyncio

_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


@pytest.fixture
async def connected_account(db_session, test_user: User):
    account = await GoogleCalendarAccountService(db_session).create_from_oauth(
        test_user.id,
        google_sub="sub-1",
        email="pessoal@example.com",
        access_token="at-1",
        refresh_token="rt-1",
        expires_in=3600,
        scope="https://www.googleapis.com/auth/calendar",
    )
    await db_session.commit()
    return account


@respx.mock
async def test_agenda_page_pulls_events_from_google(auth_client, connected_account):
    respx.get(_EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "gcal-1",
                        "summary": "Consulta médica",
                        "start": {"dateTime": "2026-06-01T14:00:00-03:00"},
                        "end": {"dateTime": "2026-06-01T15:00:00-03:00"},
                    }
                ],
                "nextSyncToken": "token-1",
            },
        )
    )
    response = await auth_client.get("/agenda")
    assert response.status_code == 200

    list_res = await auth_client.get(
        "/api/v1/events", params={"start": "2026-06-01T00:00:00", "end": "2026-06-02T00:00:00"}
    )
    titles = [e["title"] for e in list_res.json()]
    assert "Consulta médica" in titles


@respx.mock
async def test_agenda_page_renders_even_if_google_call_fails(auth_client, connected_account):
    respx.get(_EVENTS_URL).mock(side_effect=httpx.ConnectError("falha simulada de rede"))
    response = await auth_client.get("/agenda")
    assert response.status_code == 200


@respx.mock
async def test_agenda_page_skips_inactive_accounts(auth_client, db_session, test_user):
    service = GoogleCalendarAccountService(db_session)
    account = await service.create_from_oauth(
        test_user.id,
        google_sub="sub-inactive",
        email="inativa@example.com",
        access_token="at-1",
        refresh_token="rt-1",
        expires_in=3600,
        scope="https://www.googleapis.com/auth/calendar",
    )
    await service.deactivate(account)
    await db_session.commit()

    # Nenhuma rota respx é registrada para essa conta — se pull_all_accounts
    # tentasse sincronizá-la mesmo assim, a chamada não-mockada faria o
    # teste falhar (respx recusa requests sem rota correspondente).
    response = await auth_client.get("/agenda")
    assert response.status_code == 200
