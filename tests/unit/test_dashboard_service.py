"""Testes do DashboardService: agregação do 'Meu Dia'."""

from datetime import date

import pytest

from app.models.user import User
from app.schemas.task import TaskCreate
from app.services.dashboard_service import DashboardService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_my_day_empty(db_session, test_user: User):
    summary = await DashboardService(db_session).my_day(test_user.id, date(2026, 1, 1))
    assert summary.tasks_total == 0
    assert summary.progress_percent == 0
    assert summary.greeting in {"Bom dia", "Boa tarde", "Boa noite"}


async def test_my_day_computes_progress_and_minutes(db_session, test_user: User):
    task_service = TaskService(db_session)
    today = date(2026, 1, 1)
    t1 = await task_service.create(
        test_user.id, TaskCreate(title="Tarefa 1", date=today, planned_duration_minutes=30)
    )
    await task_service.create(test_user.id, TaskCreate(title="Tarefa 2", date=today, planned_duration_minutes=20))
    await task_service.complete(t1)

    summary = await DashboardService(db_session).my_day(test_user.id, today)
    assert summary.tasks_total == 2
    assert summary.tasks_done == 1
    assert summary.progress_percent == 50.0
    assert summary.planned_minutes == 50


async def test_my_day_ignores_other_dates(db_session, test_user: User):
    task_service = TaskService(db_session)
    await task_service.create(test_user.id, TaskCreate(title="Outro dia", date=date(2026, 2, 1)))

    summary = await DashboardService(db_session).my_day(test_user.id, date(2026, 1, 1))
    assert summary.tasks_total == 0
