"""Testes do StatsService: streak de dias produtivos, taxa de conclusão, tempo perdido, atrasos."""

from datetime import date, timedelta

import pytest

from app.models.user import User
from app.schemas.task import TaskCreate
from app.services.stats_service import StatsService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_summary_computes_completion_rate(db_session, test_user: User):
    today = date.today()
    service = TaskService(db_session)
    done = await service.create(test_user.id, TaskCreate(title="Feita", date=today))
    await service.complete(done)
    await service.create(test_user.id, TaskCreate(title="Pendente", date=today))

    summary = await StatsService(db_session).summary(test_user.id, today, today)
    assert summary.completion_rate_percent == 50.0


async def test_summary_counts_lost_minutes_from_cancelled(db_session, test_user: User):
    today = date.today()
    service = TaskService(db_session)
    task = await service.create(
        test_user.id, TaskCreate(title="Cancelada", date=today, planned_duration_minutes=90)
    )
    await service.cancel(task)

    summary = await StatsService(db_session).summary(test_user.id, today, today)
    assert summary.lost_minutes == 90


async def test_summary_counts_overdue_tasks(db_session, test_user: User):
    yesterday = date.today() - timedelta(days=1)
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Atrasada", date=yesterday))

    summary = await StatsService(db_session).summary(test_user.id, yesterday, yesterday)
    assert summary.overdue_tasks == 1


async def test_streak_counts_consecutive_completed_days(db_session, test_user: User):
    service = TaskService(db_session)
    today = date.today()
    for offset in range(3):
        task = await service.create(
            test_user.id, TaskCreate(title=f"Dia {offset}", date=today - timedelta(days=offset))
        )
        completed = await service.complete(task)
        completed.completed_at = completed.completed_at.replace(
            year=(today - timedelta(days=offset)).year,
            month=(today - timedelta(days=offset)).month,
            day=(today - timedelta(days=offset)).day,
        )
    await db_session.flush()

    summary = await StatsService(db_session).summary(test_user.id, today - timedelta(days=3), today)
    assert summary.streak_days == 3
