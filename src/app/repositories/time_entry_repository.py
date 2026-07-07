"""Persistência de registros de tempo (base dos Relatórios/Estatísticas)."""

import uuid
from datetime import datetime

from sqlalchemy import func, select

from app.models.category import Category
from app.models.project import Project
from app.models.role import Role
from app.models.time_entry import TimeEntry
from app.repositories.base import BaseRepository


class TimeEntryRepository(BaseRepository[TimeEntry]):
    model = TimeEntry

    async def sum_minutes_by_project(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Project.name, func.sum(TimeEntry.duration_minutes))
            .join(Project, Project.id == TimeEntry.project_id)
            .where(TimeEntry.user_id == user_id, TimeEntry.start_at >= start, TimeEntry.start_at < end)
            .group_by(Project.name)
            .order_by(func.sum(TimeEntry.duration_minutes).desc())
        )
        result = await self.session.execute(stmt)
        return [(name, int(total)) for name, total in result.all()]

    async def sum_minutes_by_category(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Category.name, func.sum(TimeEntry.duration_minutes))
            .join(Category, Category.id == TimeEntry.category_id)
            .where(TimeEntry.user_id == user_id, TimeEntry.start_at >= start, TimeEntry.start_at < end)
            .group_by(Category.name)
            .order_by(func.sum(TimeEntry.duration_minutes).desc())
        )
        result = await self.session.execute(stmt)
        return [(name, int(total)) for name, total in result.all()]

    async def sum_minutes_by_role(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Role.name, func.sum(TimeEntry.duration_minutes))
            .join(Role, Role.id == TimeEntry.role_id)
            .where(TimeEntry.user_id == user_id, TimeEntry.start_at >= start, TimeEntry.start_at < end)
            .group_by(Role.name)
            .order_by(func.sum(TimeEntry.duration_minutes).desc())
        )
        result = await self.session.execute(stmt)
        return [(name, int(total)) for name, total in result.all()]

    async def list_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime) -> list[TimeEntry]:
        stmt = (
            select(TimeEntry)
            .where(TimeEntry.user_id == user_id, TimeEntry.start_at >= start, TimeEntry.start_at < end)
            .order_by(TimeEntry.start_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def total_minutes_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime) -> int:
        stmt = select(func.coalesce(func.sum(TimeEntry.duration_minutes), 0)).where(
            TimeEntry.user_id == user_id, TimeEntry.start_at >= start, TimeEntry.start_at < end
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
