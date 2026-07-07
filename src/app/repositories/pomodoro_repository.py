"""Persistência de sessões Pomodoro."""

import uuid

from sqlalchemy import select

from app.models.enums import PomodoroStatus
from app.models.pomodoro import PomodoroSession
from app.repositories.base import BaseRepository


class PomodoroRepository(BaseRepository[PomodoroSession]):
    model = PomodoroSession

    async def get_active_for_user(self, user_id: uuid.UUID) -> PomodoroSession | None:
        stmt = select(PomodoroSession).where(
            PomodoroSession.user_id == user_id,
            PomodoroSession.status.in_([PomodoroStatus.RUNNING, PomodoroStatus.PAUSED]),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
