"""Agregação dos dados do Dashboard 'Meu Dia'."""

import uuid
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.dashboard import MyDaySummary
from app.schemas.task import TaskRead


def _greeting(now: datetime) -> str:
    hour = now.hour
    if hour < 12:
        return "Bom dia"
    if hour < 18:
        return "Boa tarde"
    return "Boa noite"


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.repo = TaskRepository(db)

    async def my_day(self, user_id: uuid.UUID, today: date | None = None) -> MyDaySummary:
        today = today or date.today()
        tasks = await self.repo.list_by_date(user_id, today)
        counts = await self.repo.counts_for_day(user_id, today)
        planned = await self.repo.sum_planned_minutes_for_day(user_id, today)
        actual = await self.repo.sum_actual_minutes_for_day(user_id, today)

        total = len(tasks)
        done = counts.get(TaskStatus.DONE.value, 0)
        progress = round((done / total) * 100, 1) if total else 0.0

        return MyDaySummary(
            today=today,
            greeting=_greeting(datetime.now()),
            tasks_total=total,
            tasks_done=done,
            progress_percent=progress,
            planned_minutes=planned,
            actual_minutes=actual,
            remaining_minutes=max(0, planned - actual),
            tasks=[TaskRead.model_validate(t) for t in tasks],
        )
