"""Testes do ReportService: agregação de tempo por projeto/categoria/papel/semana e eficiência."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.models.enums import TimeEntrySource
from app.models.user import User
from app.repositories.time_entry_repository import TimeEntryRepository
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.services.project_service import ProjectService
from app.services.report_service import ReportService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_time_by_project_aggregates_minutes(db_session, test_user: User):
    project = await ProjectService(db_session).create(test_user.id, ProjectCreate(name="Projeto X"))
    start = datetime.now(UTC) - timedelta(hours=2)
    await TimeEntryRepository(db_session).create(
        user_id=test_user.id,
        project_id=project.id,
        start_at=start,
        end_at=start + timedelta(minutes=45),
        duration_minutes=45,
        source=TimeEntrySource.MANUAL,
    )

    dataset = await ReportService(db_session).time_by_project(
        test_user.id, start - timedelta(days=1), datetime.now(UTC) + timedelta(days=1)
    )
    assert dataset.labels == ["Projeto X"]
    assert dataset.values == [45]


async def test_time_by_week_buckets_by_iso_week(db_session, test_user: User):
    start = datetime.now(UTC) - timedelta(minutes=30)
    await TimeEntryRepository(db_session).create(
        user_id=test_user.id,
        start_at=start,
        end_at=start + timedelta(minutes=30),
        duration_minutes=30,
        source=TimeEntrySource.MANUAL,
    )

    dataset = await ReportService(db_session).time_by_week(test_user.id, weeks=4)
    assert sum(dataset.values) == 30


async def test_efficiency_computes_planned_vs_actual(db_session, test_user: User):
    today = date.today()
    task = await TaskService(db_session).create(
        test_user.id, TaskCreate(title="Concluída", date=today, planned_duration_minutes=60)
    )
    await TaskService(db_session).complete(task)
    task.actual_duration_minutes = 30
    await db_session.flush()

    summary = await ReportService(db_session).efficiency(test_user.id, today, today)
    assert summary.tasks_completed == 1
    assert summary.planned_minutes == 60
    assert summary.actual_minutes == 30
    assert summary.efficiency_percent == 200.0


async def test_efficiency_with_no_completed_tasks(db_session, test_user: User):
    summary = await ReportService(db_session).efficiency(test_user.id, date.today(), date.today())
    assert summary.tasks_completed == 0
    assert summary.efficiency_percent == 0.0
