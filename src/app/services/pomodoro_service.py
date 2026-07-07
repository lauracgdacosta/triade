"""Regra de negócio do Cronômetro Pomodoro: inicia, conclui e registra tempo."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PomodoroStatus, TimeEntrySource
from app.models.pomodoro import PomodoroSession
from app.repositories.pomodoro_repository import PomodoroRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.time_entry_repository import TimeEntryRepository
from app.schemas.pomodoro import PomodoroStartRequest
from app.utils.datetime_utils import utcnow


class PomodoroService:
    def __init__(self, db: AsyncSession):
        self.repo = PomodoroRepository(db)
        self.time_entry_repo = TimeEntryRepository(db)
        self.task_repo = TaskRepository(db)

    async def get_active(self, user_id: uuid.UUID) -> PomodoroSession | None:
        return await self.repo.get_active_for_user(user_id)

    async def get(self, session_id: uuid.UUID, user_id: uuid.UUID) -> PomodoroSession | None:
        return await self.repo.get_for_user(session_id, user_id)

    async def start(self, user_id: uuid.UUID, data: PomodoroStartRequest) -> PomodoroSession:
        return await self.repo.create(
            user_id=user_id,
            task_id=data.task_id,
            mode=data.mode,
            work_minutes=data.work_minutes,
            break_minutes=data.break_minutes,
            cycles_planned=data.cycles_planned,
            cycles_completed=0,
            status=PomodoroStatus.RUNNING,
            started_at=utcnow(),
        )

    async def complete_cycle(self, session: PomodoroSession) -> PomodoroSession:
        cycles_completed = session.cycles_completed + 1
        finished = cycles_completed >= session.cycles_planned
        session = await self.repo.update(
            session,
            cycles_completed=cycles_completed,
            status=PomodoroStatus.COMPLETED if finished else PomodoroStatus.RUNNING,
            ended_at=utcnow() if finished else None,
        )
        if finished:
            await self._record_time_entry(session)
        return session

    async def cancel(self, session: PomodoroSession) -> PomodoroSession:
        session = await self.repo.update(
            session, status=PomodoroStatus.CANCELLED, ended_at=utcnow()
        )
        await self._record_time_entry(session)
        return session

    async def _record_time_entry(self, session: PomodoroSession) -> None:
        ended_at = session.ended_at or utcnow()
        duration = max(0, int((ended_at - session.started_at).total_seconds() // 60))
        await self.time_entry_repo.create(
            user_id=session.user_id,
            task_id=session.task_id,
            start_at=session.started_at,
            end_at=ended_at,
            duration_minutes=duration,
            source=TimeEntrySource.POMODORO,
        )
        if session.task_id:
            task = await self.task_repo.get(session.task_id)
            if task is not None:
                await self.task_repo.update(
                    task, actual_duration_minutes=task.actual_duration_minutes + duration
                )
