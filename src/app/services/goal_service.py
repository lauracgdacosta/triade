"""Regra de negócio de Metas, incluindo progresso calculado a partir das tarefas."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.repositories.goal_repository import GoalRepository
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate


class GoalService:
    def __init__(self, db: AsyncSession):
        self.repo = GoalRepository(db)

    async def _to_read(self, goal: Goal) -> GoalRead:
        done, total = await self.repo.task_progress(goal.id)
        data = GoalRead.model_validate(goal).model_dump()
        data["tasks_done"] = done
        data["tasks_total"] = total
        return GoalRead(**data)

    async def list(self, user_id: uuid.UUID) -> list[GoalRead]:
        goals = await self.repo.list_for_user(user_id)
        return [await self._to_read(goal) for goal in goals]

    async def get(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> Goal | None:
        return await self.repo.get_for_user(goal_id, user_id)

    async def get_read(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> GoalRead | None:
        goal = await self.get(goal_id, user_id)
        return await self._to_read(goal) if goal else None

    async def create(self, user_id: uuid.UUID, data: GoalCreate) -> Goal:
        return await self.repo.create(user_id=user_id, **data.model_dump())

    async def update(self, goal: Goal, data: GoalUpdate) -> Goal:
        return await self.repo.update(goal, **data.model_dump(exclude_unset=True))

    async def delete(self, goal: Goal) -> None:
        await self.repo.delete(goal)
