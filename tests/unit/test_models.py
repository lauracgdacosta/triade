"""Testes de models: defaults, relacionamentos e constraints básicas."""

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.base import naive_utc
from app.models.category import Category
from app.models.enums import Priority, TaskStatus
from app.models.event import Event
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_task_defaults(db_session, test_user: User):
    task = Task(user_id=test_user.id, title="Estudar SQLAlchemy")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.status == TaskStatus.PENDING
    assert task.priority == Priority.NONE
    assert task.actual_duration_minutes == 0
    assert task.date is None
    assert task.time is None


async def test_task_tags_relationship(db_session, test_user: User):
    tag = Tag(user_id=test_user.id, name="urgente")
    db_session.add(tag)
    await db_session.flush()

    task = Task(user_id=test_user.id, title="Com etiqueta")
    task.tags = [tag]
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert len(task.tags) == 1
    assert task.tags[0].name == "urgente"


async def test_category_belongs_to_user(db_session, test_user: User):
    category = Category(user_id=test_user.id, name="Trabalho")
    db_session.add(category)
    await db_session.commit()

    result = await db_session.execute(select(Category).where(Category.user_id == test_user.id))
    categories = result.scalars().all()
    assert len(categories) == 1
    assert categories[0].name == "Trabalho"


async def test_task_missing_user_id_raises(db_session):
    task = Task(user_id=uuid.uuid4(), title="Usuário inexistente")
    db_session.add(task)
    with pytest.raises(IntegrityError):
        await db_session.commit()


def test_naive_utc_strips_tzinfo_from_utc_datetime():
    aware = datetime(2026, 3, 5, 12, 0, tzinfo=UTC)
    result = naive_utc(aware)
    assert result.tzinfo is None
    assert result == datetime(2026, 3, 5, 12, 0)


def test_naive_utc_converts_non_utc_offset_before_stripping():
    minus_three = timezone(timedelta(hours=-3))
    aware = datetime(2026, 3, 5, 9, 0, tzinfo=minus_three)  # 12:00 UTC
    result = naive_utc(aware)
    assert result.tzinfo is None
    assert result == datetime(2026, 3, 5, 12, 0)


def test_naive_utc_passes_through_naive_and_none():
    naive = datetime(2026, 3, 5, 12, 0)
    assert naive_utc(naive) == naive
    assert naive_utc(None) is None


async def test_task_completed_at_assignment_strips_tzinfo(db_session, test_user: User):
    """Regressão: gravar completed_at timezone-aware quebrava no Postgres real
    (asyncpg) com "can't subtract offset-naive and offset-aware datetimes"
    — SQLite não acusa, por isso o bug só aparecia em produção."""
    task = Task(user_id=test_user.id, title="Concluir", completed_at=datetime.now(UTC))
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.completed_at.tzinfo is None


async def test_event_start_at_assignment_strips_tzinfo(db_session, test_user: User):
    start = datetime.now(UTC)
    event = Event(user_id=test_user.id, title="Reunião", start_at=start, end_at=start + timedelta(hours=1))
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    assert event.start_at.tzinfo is None
    assert event.end_at.tzinfo is None
