"""Motor de notificações on-demand: gera (idempotente) a partir de tarefas/eventos/metas."""

import uuid
from datetime import UTC, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.repositories.event_repository import EventRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.task_repository import TaskRepository
from app.utils.datetime_utils import utcnow

_EVENT_REMINDER_WINDOW = timedelta(hours=1)
_GOAL_DEADLINE_WINDOW = timedelta(days=3)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)
        self.task_repo = TaskRepository(db)
        self.event_repo = EventRepository(db)
        self.goal_repo = GoalRepository(db)

    async def generate_pending(self, user_id: uuid.UUID) -> None:
        """Cria notificações para tarefas vencidas, eventos próximos e metas com prazo perto.

        Idempotente: não duplica se já existe uma notificação igual (mesmo tipo e
        título) criada hoje — não há FK para a entidade de origem no schema atual,
        então o título (que embute o nome da entidade) é a chave de dedupe.
        """
        # `now`/`event_window_end` são naive (comparados a Event.start_at/end_at,
        # que não são timezone-aware no Postgres); `day_start` é aware porque
        # é comparado a Notification.created_at, que É timezone-aware.
        now = utcnow()
        today = now.date()
        day_start = datetime.combine(today, time.min, tzinfo=UTC)
        event_window_end = now + _EVENT_REMINDER_WINDOW

        for task in await self.task_repo.list_overdue(user_id, today):
            title = f"Tarefa vencida: {task.title}"
            if not await self.repo.exists_since(user_id, NotificationType.TASK_DUE, title, day_start):
                await self.repo.create(
                    user_id=user_id,
                    type=NotificationType.TASK_DUE,
                    title=title,
                    message=f"Venceu em {task.date.strftime('%d/%m/%Y')}.",
                    read=False,
                )

        for event in await self.event_repo.list_in_range(user_id, now, event_window_end):
            if event.all_day:
                continue
            title = f"Compromisso em breve: {event.title}"
            if not await self.repo.exists_since(user_id, NotificationType.EVENT_REMINDER, title, day_start):
                await self.repo.create(
                    user_id=user_id,
                    type=NotificationType.EVENT_REMINDER,
                    title=title,
                    message=f"Às {event.start_at.strftime('%H:%M')}.",
                    read=False,
                )

        deadline_cutoff = today + _GOAL_DEADLINE_WINDOW
        for goal in await self.goal_repo.list_upcoming_deadlines(user_id, today, deadline_cutoff):
            title = f"Meta com prazo próximo: {goal.title}"
            if not await self.repo.exists_since(user_id, NotificationType.GOAL_DEADLINE, title, day_start):
                await self.repo.create(
                    user_id=user_id,
                    type=NotificationType.GOAL_DEADLINE,
                    title=title,
                    message=f"Prazo em {goal.deadline.strftime('%d/%m/%Y')}.",
                    read=False,
                )

    async def list(self, user_id: uuid.UUID) -> list[Notification]:
        return await self.repo.list_for_user(user_id, limit=30)

    async def count_unread(self, user_id: uuid.UUID) -> int:
        return await self.repo.count_unread(user_id)

    async def get(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
        return await self.repo.get_for_user(notification_id, user_id)

    async def mark_read(self, notification: Notification) -> Notification:
        return await self.repo.update(notification, read=True)

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self.repo.mark_all_read(user_id)
