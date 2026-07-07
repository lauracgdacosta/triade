"""Persistência de Tarefas: filtros por data, status, kanban e busca textual."""

import uuid
from datetime import date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.enums import TaskStatus
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    model = Task

    def _base_stmt(self, user_id: uuid.UUID):
        return select(Task).options(selectinload(Task.tags), selectinload(Task.attachments)).where(
            Task.user_id == user_id
        )

    async def get_for_user(self, id_: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        stmt = self._base_stmt(user_id).where(Task.id == id_)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_date(self, user_id: uuid.UUID, day: date) -> list[Task]:
        stmt = self._base_stmt(user_id).where(Task.date == day).order_by(Task.time.asc().nulls_last())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_between_dates(self, user_id: uuid.UUID, start: date, end: date) -> list[Task]:
        stmt = self._base_stmt(user_id).where(Task.date >= start, Task.date <= end).order_by(Task.date, Task.time)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_status(self, user_id: uuid.UUID, status: TaskStatus) -> list[Task]:
        stmt = self._base_stmt(user_id).where(Task.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_kanban_column(self, user_id: uuid.UUID, column_id: uuid.UUID) -> list[Task]:
        stmt = self._base_stmt(user_id).where(Task.kanban_column_id == column_id).order_by(
            Task.kanban_position
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_overdue(self, user_id: uuid.UUID, today: date) -> list[Task]:
        stmt = self._base_stmt(user_id).where(
            Task.date < today,
            Task.status.not_in([TaskStatus.DONE, TaskStatus.CANCELLED, TaskStatus.ARCHIVED]),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_completed_at_dates(self, user_id: uuid.UUID, since: datetime) -> list[date]:
        stmt = select(Task.completed_at).where(
            Task.user_id == user_id, Task.status == TaskStatus.DONE, Task.completed_at >= since
        )
        result = await self.session.execute(stmt)
        return sorted({completed_at.date() for (completed_at,) in result.all()})

    async def search(self, user_id: uuid.UUID, query: str) -> list[Task]:
        like = f"%{query}%"
        stmt = self._base_stmt(user_id).where(
            or_(Task.title.ilike(like), Task.description.ilike(like), Task.notes.ilike(like))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def counts_for_day(self, user_id: uuid.UUID, day: date) -> dict[str, int]:
        stmt = select(Task.status, func.count(Task.id)).where(
            Task.user_id == user_id, Task.date == day
        ).group_by(Task.status)
        result = await self.session.execute(stmt)
        return {status.value: count for status, count in result.all()}

    async def sum_planned_minutes_for_day(self, user_id: uuid.UUID, day: date) -> int:
        stmt = select(func.coalesce(func.sum(Task.planned_duration_minutes), 0)).where(
            Task.user_id == user_id, Task.date == day
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def sum_actual_minutes_for_day(self, user_id: uuid.UUID, day: date) -> int:
        stmt = select(func.coalesce(func.sum(Task.actual_duration_minutes), 0)).where(
            Task.user_id == user_id, Task.date == day
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
