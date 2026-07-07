"""Persistência de Metas, incluindo agregação de progresso a partir das tarefas."""

import uuid
from datetime import date

from sqlalchemy import func, or_, select

from app.models.enums import TaskStatus
from app.models.goal import Goal
from app.models.task import Task
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    model = Goal

    async def search(self, user_id: uuid.UUID, query: str) -> list[Goal]:
        like = f"%{query}%"
        stmt = select(Goal).where(
            Goal.user_id == user_id, or_(Goal.title.ilike(like), Goal.description.ilike(like))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_upcoming_deadlines(self, user_id: uuid.UUID, start: date, end: date) -> list[Goal]:
        stmt = select(Goal).where(
            Goal.user_id == user_id,
            Goal.deadline.is_not(None),
            Goal.deadline >= start,
            Goal.deadline <= end,
            Goal.percent_complete < 100,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def task_progress(self, goal_id: uuid.UUID) -> tuple[int, int]:
        """Retorna (concluídas, total) de tarefas vinculadas à meta."""
        stmt = select(
            func.count(Task.id),
            func.count(Task.id).filter(Task.status == TaskStatus.DONE),
        ).where(Task.goal_id == goal_id)
        result = await self.session.execute(stmt)
        total, done = result.one()
        return done or 0, total or 0
