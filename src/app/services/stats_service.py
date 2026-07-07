"""Estatísticas avançadas: streak de dias produtivos, taxa de conclusão, tempo perdido, atrasos."""

import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.report import StatsSummary
from app.utils.datetime_utils import utcnow

_STREAK_LOOKBACK_DAYS = 90


class StatsService:
    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)

    async def summary(self, user_id: uuid.UUID, start: date, end: date) -> StatsSummary:
        tasks = await self.task_repo.list_between_dates(user_id, start, end)
        done = [t for t in tasks if t.status == TaskStatus.DONE]
        cancelled = [t for t in tasks if t.status == TaskStatus.CANCELLED]
        completion_rate = round(len(done) / len(tasks) * 100, 1) if tasks else 0.0
        lost_minutes = sum(t.planned_duration_minutes or 0 for t in cancelled)
        overdue = await self.task_repo.list_overdue(user_id, date.today())
        streak = await self._current_streak(user_id)
        return StatsSummary(
            streak_days=streak,
            completion_rate_percent=completion_rate,
            lost_minutes=lost_minutes,
            overdue_tasks=len(overdue),
        )

    async def _current_streak(self, user_id: uuid.UUID) -> int:
        since = utcnow() - timedelta(days=_STREAK_LOOKBACK_DAYS)
        productive_dates = set(await self.task_repo.list_completed_at_dates(user_id, since))
        streak = 0
        cursor = date.today()
        while cursor in productive_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak
