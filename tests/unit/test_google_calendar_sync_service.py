"""Testes do GoogleCalendarSyncService: pull incremental/full sync e push."""

from datetime import datetime

import httpx
import pytest
import respx

from app.models.user import User
from app.schemas.event import EventCreate
from app.services.event_service import EventService
from app.services.google_calendar_account_service import GoogleCalendarAccountService
from app.services.google_calendar_sync_service import GoogleCalendarSyncService

pytestmark = pytest.mark.asyncio

_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


async def _connected_account(db_session, user_id):
    return await GoogleCalendarAccountService(db_session).create_from_oauth(
        user_id,
        google_sub="sub-1",
        email="trabalho@example.com",
        access_token="at-1",
        refresh_token="rt-1",
        expires_in=3600,
        scope="https://www.googleapis.com/auth/calendar",
    )


@respx.mock
async def test_pull_account_full_sync_creates_events_and_saves_token(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    respx.get(_EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "gcal-1",
                        "summary": "Reunião de time",
                        "start": {"dateTime": "2026-01-10T09:00:00-03:00"},
                        "end": {"dateTime": "2026-01-10T10:00:00-03:00"},
                    }
                ],
                "nextSyncToken": "sync-token-1",
            },
        )
    )

    sync = GoogleCalendarSyncService(db_session)
    await sync.pull_account(account)

    events = await sync.events.list_in_range(test_user.id, datetime(2026, 1, 1), datetime(2026, 1, 31))
    assert len(events) == 1
    assert events[0].title == "Reunião de time"
    assert events[0].google_event_id == "gcal-1"
    # start.dateTime -03:00 -> 12:00 UTC naive
    assert events[0].start_at == datetime(2026, 1, 10, 12, 0)

    refreshed = await sync.accounts.get(account.id, test_user.id)
    assert refreshed.sync_token == "sync-token-1"
    assert refreshed.last_synced_at is not None


@respx.mock
async def test_pull_account_incremental_uses_sync_token(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    account = await GoogleCalendarAccountService(db_session).record_sync(
        account, sync_token="old-token", synced_at=datetime.now()
    )

    route = respx.get(_EVENTS_URL).mock(return_value=httpx.Response(200, json={"items": [], "nextSyncToken": "new-token"}))

    await GoogleCalendarSyncService(db_session).pull_account(account)

    assert route.calls.last.request.url.params["syncToken"] == "old-token"


@respx.mock
async def test_pull_account_410_forces_full_resync(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    account = await GoogleCalendarAccountService(db_session).record_sync(
        account, sync_token="stale-token", synced_at=datetime.now()
    )

    route = respx.get(_EVENTS_URL).mock(
        side_effect=[
            httpx.Response(410, json={"error": {"message": "Sync token expired"}}),
            httpx.Response(200, json={"items": [], "nextSyncToken": "fresh-token"}),
        ]
    )

    await GoogleCalendarSyncService(db_session).pull_account(account)

    assert route.call_count == 2
    second_call_params = route.calls[1].request.url.params
    assert "syncToken" not in second_call_params
    assert "timeMin" in second_call_params

    refreshed = await GoogleCalendarAccountService(db_session).get(account.id, test_user.id)
    assert refreshed.sync_token == "fresh-token"


@respx.mock
async def test_pull_account_cancelled_status_deletes_local_event(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    sync = GoogleCalendarSyncService(db_session)
    await sync.events.create(
        user_id=test_user.id,
        title="Será removido",
        start_at=datetime(2026, 1, 10, 9),
        end_at=datetime(2026, 1, 10, 10),
        google_account_id=account.id,
        google_event_id="gcal-remover",
    )

    respx.get(_EVENTS_URL).mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "gcal-remover", "status": "cancelled"}], "nextSyncToken": "t"}
        )
    )
    await sync.pull_account(account)

    events = await sync.events.list_in_range(test_user.id, datetime(2026, 1, 1), datetime(2026, 1, 31))
    assert events == []


@respx.mock
async def test_pull_account_all_day_event_subtracts_exclusive_end_date(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    respx.get(_EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "gcal-allday",
                        "summary": "Feriado",
                        "start": {"date": "2026-03-01"},
                        "end": {"date": "2026-03-02"},
                    }
                ],
                "nextSyncToken": "t",
            },
        )
    )
    sync = GoogleCalendarSyncService(db_session)
    await sync.pull_account(account)

    events = await sync.events.list_in_range(test_user.id, datetime(2026, 2, 28), datetime(2026, 3, 3))
    assert len(events) == 1
    assert events[0].all_day is True
    assert events[0].start_at.date() == events[0].end_at.date()


async def test_push_create_skips_events_without_google_account(db_session, test_user: User):
    event, _ = await EventService(db_session).create(
        test_user.id,
        EventCreate(title="Local", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    result = await GoogleCalendarSyncService(db_session).push_create(event)
    assert result.google_event_id is None


async def test_push_create_skips_recurring_events(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    event, _ = await EventService(db_session).create(
        test_user.id,
        EventCreate(
            title="Recorrente",
            start_at=datetime(2026, 1, 10, 9),
            end_at=datetime(2026, 1, 10, 10),
            recurrence_rule="FREQ=WEEKLY",
        ),
    )
    event.google_account_id = account.id
    await db_session.flush()

    result = await GoogleCalendarSyncService(db_session).push_create(event)
    assert result.google_event_id is None


@respx.mock
async def test_push_create_inserts_event_and_saves_google_id(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    route = respx.post(_EVENTS_URL).mock(return_value=httpx.Response(200, json={"id": "gcal-novo"}))

    event, _ = await EventService(db_session).create(
        test_user.id,
        EventCreate(title="Sincronizar", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    event.google_account_id = account.id
    await db_session.flush()

    result = await GoogleCalendarSyncService(db_session).push_create(event)
    assert result.google_event_id == "gcal-novo"
    assert result.google_synced_at is not None
    body = route.calls.last.request.content
    assert b"Sincronizar" in body


@respx.mock
async def test_push_update_falls_back_to_create_without_google_event_id(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    respx.post(_EVENTS_URL).mock(return_value=httpx.Response(200, json={"id": "gcal-criado-na-edicao"}))

    event, _ = await EventService(db_session).create(
        test_user.id,
        EventCreate(title="Editar sem id ainda", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    event.google_account_id = account.id
    await db_session.flush()

    result = await GoogleCalendarSyncService(db_session).push_update(event)
    assert result.google_event_id == "gcal-criado-na-edicao"


@respx.mock
async def test_push_delete_calls_google_delete(db_session, test_user: User):
    account = await _connected_account(db_session, test_user.id)
    route = respx.delete(f"{_EVENTS_URL}/gcal-1").mock(return_value=httpx.Response(204))

    event, _ = await EventService(db_session).create(
        test_user.id,
        EventCreate(title="Excluir", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    event.google_account_id = account.id
    event.google_event_id = "gcal-1"
    await db_session.flush()

    await GoogleCalendarSyncService(db_session).push_delete(event)
    assert route.called
