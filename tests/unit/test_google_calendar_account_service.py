"""Testes do GoogleCalendarAccountService: criptografia, refresh e desconexão."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from app.models.user import User
from app.schemas.event import EventCreate
from app.services.event_service import EventService
from app.services.google_calendar_account_service import GoogleCalendarAccountService
from app.services.google_calendar_client import GoogleCalendarError

pytestmark = pytest.mark.asyncio


async def _connect(service: GoogleCalendarAccountService, user_id, *, expires_in: int = 3600):
    return await service.create_from_oauth(
        user_id,
        google_sub="sub-123",
        email="trabalho@example.com",
        access_token="access-token-1",
        refresh_token="refresh-token-1",
        expires_in=expires_in,
        scope="https://www.googleapis.com/auth/calendar",
    )


async def test_create_from_oauth_stores_tokens_encrypted(db_session, test_user: User):
    service = GoogleCalendarAccountService(db_session)
    account = await _connect(service, test_user.id)
    assert account.access_token_encrypted != "access-token-1"
    assert account.refresh_token_encrypted != "refresh-token-1"
    assert account.email == "trabalho@example.com"
    assert account.is_active is True


async def test_create_from_oauth_reconnect_reuses_same_row(db_session, test_user: User):
    service = GoogleCalendarAccountService(db_session)
    first = await _connect(service, test_user.id)
    await service.deactivate(first)

    second = await _connect(service, test_user.id)
    assert second.id == first.id
    assert second.is_active is True


async def test_get_valid_access_token_no_refresh_when_not_expired(db_session, test_user: User):
    service = GoogleCalendarAccountService(db_session)
    account = await _connect(service, test_user.id, expires_in=3600)

    token = await service.get_valid_access_token(account)
    assert token == "access-token-1"


@respx.mock
async def test_get_valid_access_token_refreshes_when_expired(db_session, test_user: User):
    service = GoogleCalendarAccountService(db_session)
    account = await _connect(service, test_user.id, expires_in=-10)

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "access-token-2", "expires_in": 3600})
    )
    token = await service.get_valid_access_token(account)
    assert token == "access-token-2"
    expires_at = account.token_expires_at.replace(tzinfo=UTC) if account.token_expires_at.tzinfo is None else account.token_expires_at
    assert expires_at > datetime.now(UTC) + timedelta(minutes=59)


@respx.mock
async def test_get_valid_access_token_deactivates_on_invalid_grant(db_session, test_user: User):
    service = GoogleCalendarAccountService(db_session)
    account = await _connect(service, test_user.id, expires_in=-10)

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(400, json={"error": "invalid_grant"})
    )
    with pytest.raises(GoogleCalendarError):
        await service.get_valid_access_token(account)
    assert account.is_active is False


async def test_disconnect_clears_google_fields_on_linked_events(db_session, test_user: User):
    account_service = GoogleCalendarAccountService(db_session)
    account = await _connect(account_service, test_user.id)

    event_service = EventService(db_session)
    event, _ = await event_service.create(
        test_user.id,
        EventCreate(title="Reunião", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    event.google_account_id = account.id
    event.google_event_id = "gcal-1"
    event.google_synced_at = datetime.now(UTC)
    await db_session.flush()

    await account_service.disconnect(account)
    await db_session.refresh(event)

    assert event.google_account_id is None
    assert event.google_event_id is None
    assert event.google_synced_at is None
    assert await account_service.get(account.id, test_user.id) is None
