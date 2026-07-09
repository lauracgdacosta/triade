"""Testes do cliente HTTP do Google Calendar (OAuth2 + API v3), mockado com respx."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.config import get_settings
from app.services import google_calendar_client as client

pytestmark = pytest.mark.asyncio

get_settings().google_client_id = "test-client-id"
get_settings().google_client_secret = "test-client-secret"
get_settings().google_oauth_redirect_url = "http://localhost:8000/integrations/google/callback"


def test_authorization_url_includes_required_params():
    url = client.authorization_url("opaque-state")
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "client_id=test-client-id" in url
    assert "state=opaque-state" in url
    assert "calendar" in url


@respx.mock
async def test_exchange_code_returns_tokens():
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "at-123",
                "refresh_token": "rt-456",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/calendar",
                "token_type": "Bearer",
            },
        )
    )
    result = await client.exchange_code("some-code")
    assert result["access_token"] == "at-123"
    assert result["refresh_token"] == "rt-456"


@respx.mock
async def test_exchange_code_error_raises_google_calendar_error():
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(400, json={"error": "invalid_grant", "error_description": "Bad code"})
    )
    with pytest.raises(client.GoogleCalendarError) as exc_info:
        await client.exchange_code("bad-code")
    assert exc_info.value.status_code == 400
    assert "Bad code" in exc_info.value.message


@respx.mock
async def test_refresh_access_token():
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "new-at", "expires_in": 3600})
    )
    result = await client.refresh_access_token("rt-456")
    assert result["access_token"] == "new-at"


@respx.mock
async def test_get_userinfo():
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(200, json={"sub": "1234567890", "email": "user@example.com"})
    )
    result = await client.get_userinfo("at-123")
    assert result["email"] == "user@example.com"


@respx.mock
async def test_list_events_full_sync_uses_time_min_max():
    route = respx.get("https://www.googleapis.com/calendar/v3/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": [], "nextSyncToken": "sync-abc"})
    )
    result = await client.list_events(
        "at-123", "primary", time_min=datetime(2026, 1, 1), time_max=datetime(2026, 12, 31)
    )
    assert result["nextSyncToken"] == "sync-abc"
    request = route.calls.last.request
    assert "timeMin" in request.url.params
    assert "timeMax" in request.url.params
    assert request.url.params["singleEvents"] == "true"


@respx.mock
async def test_list_events_full_sync_accepts_timezone_aware_bounds():
    """Regressão: GoogleCalendarSyncService.pull_account passa datetimes
    aware (datetime.now(UTC) +/- timedelta). `.isoformat() + "Z"` ingênuo
    produz "...+00:00Z" (offset duplicado) para esse caso, e o Google
    rejeita com 400 Bad Request — só reproduzia em produção, nunca com os
    datetimes naive usados no teste acima."""
    route = respx.get("https://www.googleapis.com/calendar/v3/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    await client.list_events(
        "at-123", "primary", time_min=datetime(2026, 1, 1, tzinfo=UTC), time_max=datetime(2026, 12, 31, tzinfo=UTC)
    )
    request = route.calls.last.request
    assert request.url.params["timeMin"] == "2026-01-01T00:00:00Z"
    assert request.url.params["timeMax"] == "2026-12-31T00:00:00Z"


@respx.mock
async def test_list_events_incremental_uses_sync_token():
    route = respx.get("https://www.googleapis.com/calendar/v3/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    await client.list_events("at-123", "primary", sync_token="sync-abc")
    request = route.calls.last.request
    assert request.url.params["syncToken"] == "sync-abc"
    assert "timeMin" not in request.url.params


@respx.mock
async def test_list_events_410_raises_error_with_status_code():
    respx.get("https://www.googleapis.com/calendar/v3/calendars/primary/events").mock(
        return_value=httpx.Response(410, json={"error": {"message": "Sync token expired"}})
    )
    with pytest.raises(client.GoogleCalendarError) as exc_info:
        await client.list_events("at-123", "primary", sync_token="stale-token")
    assert exc_info.value.status_code == 410


@respx.mock
async def test_list_events_page():
    respx.get("https://www.googleapis.com/calendar/v3/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": [], "nextSyncToken": "sync-final"})
    )
    result = await client.list_events_page("at-123", "primary", "page-2")
    assert result["nextSyncToken"] == "sync-final"


@respx.mock
async def test_insert_event():
    respx.post("https://www.googleapis.com/calendar/v3/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"id": "gcal-event-1"})
    )
    result = await client.insert_event("at-123", "primary", {"summary": "Reunião"})
    assert result["id"] == "gcal-event-1"


@respx.mock
async def test_update_event():
    respx.patch("https://www.googleapis.com/calendar/v3/calendars/primary/events/gcal-event-1").mock(
        return_value=httpx.Response(200, json={"id": "gcal-event-1", "summary": "Atualizado"})
    )
    result = await client.update_event("at-123", "primary", "gcal-event-1", {"summary": "Atualizado"})
    assert result["summary"] == "Atualizado"


@respx.mock
async def test_delete_event_success():
    respx.delete("https://www.googleapis.com/calendar/v3/calendars/primary/events/gcal-event-1").mock(
        return_value=httpx.Response(204)
    )
    await client.delete_event("at-123", "primary", "gcal-event-1")


@respx.mock
async def test_delete_event_404_is_idempotent():
    respx.delete("https://www.googleapis.com/calendar/v3/calendars/primary/events/gone").mock(
        return_value=httpx.Response(404)
    )
    await client.delete_event("at-123", "primary", "gone")
