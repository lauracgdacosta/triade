"""Testes do NotificationService: geração idempotente a partir de tarefas/eventos/metas."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.models.user import User
from app.schemas.event import EventCreate
from app.schemas.goal import GoalCreate
from app.schemas.task import TaskCreate
from app.services.event_service import EventService
from app.services.goal_service import GoalService
from app.services.notification_service import NotificationService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_generate_pending_creates_notification_for_overdue_task(db_session, test_user: User):
    yesterday = date.today() - timedelta(days=1)
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Atrasada", date=yesterday))

    service = NotificationService(db_session)
    await service.generate_pending(test_user.id)
    notifications = await service.list(test_user.id)

    assert len(notifications) == 1
    assert "Atrasada" in notifications[0].title


async def test_generate_pending_is_idempotent(db_session, test_user: User):
    yesterday = date.today() - timedelta(days=1)
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Atrasada", date=yesterday))

    service = NotificationService(db_session)
    await service.generate_pending(test_user.id)
    await service.generate_pending(test_user.id)
    notifications = await service.list(test_user.id)

    assert len(notifications) == 1


async def test_generate_pending_creates_notification_for_upcoming_event(db_session, test_user: User):
    start = datetime.now(UTC) + timedelta(minutes=30)
    await EventService(db_session).create(
        test_user.id, EventCreate(title="Reunião", start_at=start, end_at=start + timedelta(hours=1))
    )

    service = NotificationService(db_session)
    await service.generate_pending(test_user.id)
    notifications = await service.list(test_user.id)

    assert any("Reunião" in n.title for n in notifications)


async def test_generate_pending_creates_notification_for_goal_deadline(db_session, test_user: User):
    deadline = date.today() + timedelta(days=2)
    await GoalService(db_session).create(test_user.id, GoalCreate(title="Meta próxima", deadline=deadline))

    service = NotificationService(db_session)
    await service.generate_pending(test_user.id)
    notifications = await service.list(test_user.id)

    assert any("Meta próxima" in n.title for n in notifications)


async def test_mark_read_and_count_unread(db_session, test_user: User):
    yesterday = date.today() - timedelta(days=1)
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Atrasada", date=yesterday))

    service = NotificationService(db_session)
    await service.generate_pending(test_user.id)
    assert await service.count_unread(test_user.id) == 1

    notifications = await service.list(test_user.id)
    await service.mark_read(notifications[0])
    assert await service.count_unread(test_user.id) == 0


async def test_mark_all_read(db_session, test_user: User):
    yesterday = date.today() - timedelta(days=1)
    await TaskService(db_session).create(test_user.id, TaskCreate(title="A", date=yesterday))
    await TaskService(db_session).create(test_user.id, TaskCreate(title="B", date=yesterday))

    service = NotificationService(db_session)
    await service.generate_pending(test_user.id)
    assert await service.count_unread(test_user.id) == 2

    await service.mark_all_read(test_user.id)
    assert await service.count_unread(test_user.id) == 0
