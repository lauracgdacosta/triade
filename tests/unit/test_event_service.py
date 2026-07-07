"""Testes do EventService: CRUD e detecção de conflito de horário."""

from datetime import UTC, datetime

import pytest

from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate
from app.services.event_service import EventService

pytestmark = pytest.mark.asyncio


async def test_create_event_without_conflict(db_session, test_user: User):
    service = EventService(db_session)
    event, conflict = await service.create(
        test_user.id,
        EventCreate(title="Reunião", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    assert event.title == "Reunião"
    assert conflict is False


async def test_overlapping_events_flagged_as_conflict(db_session, test_user: User):
    service = EventService(db_session)
    await service.create(
        test_user.id,
        EventCreate(title="Primeiro", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    _, conflict = await service.create(
        test_user.id,
        EventCreate(title="Segundo", start_at=datetime(2026, 1, 10, 9, 30), end_at=datetime(2026, 1, 10, 10, 30)),
    )
    assert conflict is True


async def test_non_overlapping_events_no_conflict(db_session, test_user: User):
    service = EventService(db_session)
    await service.create(
        test_user.id,
        EventCreate(title="Primeiro", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    _, conflict = await service.create(
        test_user.id,
        EventCreate(title="Segundo", start_at=datetime(2026, 1, 10, 10), end_at=datetime(2026, 1, 10, 11)),
    )
    assert conflict is False


async def test_update_event_excludes_itself_from_conflict_check(db_session, test_user: User):
    service = EventService(db_session)
    event, _ = await service.create(
        test_user.id,
        EventCreate(title="Único", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    updated, conflict = await service.update(event, EventUpdate(title="Único renomeado"))
    assert conflict is False
    assert updated.title == "Único renomeado"


async def test_list_in_range(db_session, test_user: User):
    service = EventService(db_session)
    await service.create(
        test_user.id,
        EventCreate(title="Dentro", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    await service.create(
        test_user.id,
        EventCreate(title="Fora", start_at=datetime(2026, 2, 1, 9), end_at=datetime(2026, 2, 1, 10)),
    )
    results = await service.list_in_range(test_user.id, datetime(2026, 1, 1), datetime(2026, 1, 31))
    assert len(results) == 1
    assert results[0].title == "Dentro"


async def test_list_in_range_accepts_timezone_aware_bounds(db_session, test_user: User):
    """Regressão: o FullCalendar (Agenda) manda start/end com timezone (ex.:
    `.toISOString()`, offset -03:00 etc.). Isso quebrava contra Postgres real
    ("can't subtract offset-naive and offset-aware datetimes") — SQLite não
    acusa, por isso o teste precisa checar explicitamente que o service
    aceita e normaliza datas com tzinfo, não só que a query "funciona"."""
    service = EventService(db_session)
    await service.create(
        test_user.id,
        EventCreate(title="Dentro", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    results = await service.list_in_range(
        test_user.id, datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC)
    )
    assert len(results) == 1


async def test_has_conflict_accepts_timezone_aware_bounds(db_session, test_user: User):
    service = EventService(db_session)
    await service.create(
        test_user.id,
        EventCreate(title="Existente", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10)),
    )
    conflict = await service.has_conflict(
        test_user.id, datetime(2026, 1, 10, 9, 30, tzinfo=UTC), datetime(2026, 1, 10, 10, 30, tzinfo=UTC)
    )
    assert conflict is True


async def test_event_start_end_stored_naive_even_from_aware_input(db_session, test_user: User):
    service = EventService(db_session)
    start = datetime(2026, 1, 10, 9, tzinfo=UTC)
    event, _ = await service.create(
        test_user.id, EventCreate(title="Aware", start_at=start, end_at=datetime(2026, 1, 10, 10, tzinfo=UTC))
    )
    assert event.start_at.tzinfo is None
