"""Testes do PomodoroService: início, conclusão de ciclo e registro de tempo."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.enums import PomodoroStatus, TimeEntrySource
from app.models.user import User
from app.repositories.time_entry_repository import TimeEntryRepository
from app.schemas.pomodoro import PomodoroStartRequest
from app.schemas.task import TaskCreate
from app.services.pomodoro_service import PomodoroService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_start_session(db_session, test_user: User):
    service = PomodoroService(db_session)
    session = await service.start(
        test_user.id, PomodoroStartRequest(mode="25_5", work_minutes=25, break_minutes=5, cycles_planned=1)
    )
    assert session.status == PomodoroStatus.RUNNING
    assert session.cycles_completed == 0


async def test_complete_single_cycle_marks_completed_and_records_time(db_session, test_user: User):
    service = PomodoroService(db_session)
    session = await service.start(
        test_user.id, PomodoroStartRequest(mode="25_5", work_minutes=25, break_minutes=5, cycles_planned=1)
    )
    # simula que o ciclo já rodou por 30 minutos
    session.started_at = datetime.now(UTC) - timedelta(minutes=30)
    await db_session.flush()

    finished = await service.complete_cycle(session)
    assert finished.status == PomodoroStatus.COMPLETED
    assert finished.cycles_completed == 1
    assert finished.ended_at is not None

    entries = await TimeEntryRepository(db_session).list_in_range(
        test_user.id, datetime.now(UTC) - timedelta(hours=1), datetime.now(UTC) + timedelta(hours=1)
    )
    assert len(entries) == 1
    assert entries[0].source == TimeEntrySource.POMODORO


async def test_multi_cycle_session_only_completes_after_last_cycle(db_session, test_user: User):
    service = PomodoroService(db_session)
    session = await service.start(
        test_user.id, PomodoroStartRequest(mode="25_5", work_minutes=25, break_minutes=5, cycles_planned=2)
    )
    after_first = await service.complete_cycle(session)
    assert after_first.status == PomodoroStatus.RUNNING
    assert after_first.cycles_completed == 1

    after_second = await service.complete_cycle(after_first)
    assert after_second.status == PomodoroStatus.COMPLETED
    assert after_second.cycles_completed == 2


async def test_cancel_session_records_partial_time(db_session, test_user: User):
    service = PomodoroService(db_session)
    session = await service.start(
        test_user.id, PomodoroStartRequest(mode="25_5", work_minutes=25, break_minutes=5, cycles_planned=1)
    )
    cancelled = await service.cancel(session)
    assert cancelled.status == PomodoroStatus.CANCELLED

    entries = await TimeEntryRepository(db_session).list_in_range(
        test_user.id, datetime.now(UTC) - timedelta(hours=1), datetime.now(UTC) + timedelta(hours=1)
    )
    assert len(entries) == 1


async def test_pomodoro_updates_task_actual_duration(db_session, test_user: User):
    task_service = TaskService(db_session)
    task = await task_service.create(test_user.id, TaskCreate(title="Com pomodoro"))

    pomodoro_service = PomodoroService(db_session)
    session = await pomodoro_service.start(
        test_user.id,
        PomodoroStartRequest(mode="25_5", work_minutes=25, break_minutes=5, cycles_planned=1, task_id=task.id),
    )
    session.started_at = datetime.now(UTC) - timedelta(minutes=25)
    await db_session.flush()
    await pomodoro_service.complete_cycle(session)

    refreshed = await task_service.get(task.id, test_user.id)
    assert refreshed.actual_duration_minutes >= 24
