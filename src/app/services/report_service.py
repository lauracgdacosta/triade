"""Agregação de Relatórios (tempo por projeto/categoria/papel/semana, eficiência)."""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.time_entry_repository import TimeEntryRepository
from app.schemas.report import ChartDataset, ReportSummary
from app.utils.datetime_utils import utcnow


class ReportService:
    def __init__(self, db: AsyncSession):
        self.time_entry_repo = TimeEntryRepository(db)
        self.task_repo = TaskRepository(db)

    async def time_by_project(self, user_id: uuid.UUID, start: datetime, end: datetime) -> ChartDataset:
        rows = await self.time_entry_repo.sum_minutes_by_project(user_id, start, end)
        return ChartDataset(labels=[name for name, _ in rows], values=[minutes for _, minutes in rows])

    async def time_by_category(self, user_id: uuid.UUID, start: datetime, end: datetime) -> ChartDataset:
        rows = await self.time_entry_repo.sum_minutes_by_category(user_id, start, end)
        return ChartDataset(labels=[name for name, _ in rows], values=[minutes for _, minutes in rows])

    async def time_by_role(self, user_id: uuid.UUID, start: datetime, end: datetime) -> ChartDataset:
        rows = await self.time_entry_repo.sum_minutes_by_role(user_id, start, end)
        return ChartDataset(labels=[name for name, _ in rows], values=[minutes for _, minutes in rows])

    async def time_by_week(self, user_id: uuid.UUID, weeks: int = 8) -> ChartDataset:
        end = utcnow()
        start = end - timedelta(weeks=weeks)
        entries = await self.time_entry_repo.list_in_range(user_id, start, end)
        buckets: dict[str, int] = {}
        for entry in entries:
            iso_year, iso_week, _ = entry.start_at.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            buckets[key] = buckets.get(key, 0) + entry.duration_minutes
        labels = sorted(buckets)
        return ChartDataset(labels=labels, values=[buckets[label] for label in labels])

    async def efficiency(self, user_id: uuid.UUID, start: date, end: date) -> ReportSummary:
        tasks = await self.task_repo.list_between_dates(user_id, start, end)
        done = [t for t in tasks if t.status == TaskStatus.DONE]
        planned = sum(t.planned_duration_minutes or 0 for t in done)
        actual = sum(t.actual_duration_minutes for t in done)
        efficiency_percent = round(planned / actual * 100, 1) if actual else 0.0
        avg_minutes = round(actual / len(done), 1) if done else 0.0
        return ReportSummary(
            tasks_completed=len(done),
            planned_minutes=planned,
            actual_minutes=actual,
            efficiency_percent=efficiency_percent,
            avg_minutes_per_task=avg_minutes,
        )
