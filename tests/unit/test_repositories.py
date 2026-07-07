"""Testes do Repository Pattern: operações genéricas e filtros específicos de Task."""

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import TaskStatus
from app.models.role import Role
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.task_repository import TaskRepository

pytestmark = pytest.mark.asyncio


async def test_base_repository_create_update_delete(db_session, test_user: User):
    repo = RoleRepository(db_session)
    role = await repo.create(user_id=test_user.id, name="Estudos", color="#000000", icon="fa-book")
    assert role.id is not None

    fetched = await repo.get_for_user(role.id, test_user.id)
    assert fetched is not None

    updated = await repo.update(role, name="Estudos avançados")
    assert updated.name == "Estudos avançados"

    count = await repo.count_for_user(test_user.id)
    assert count == 1

    await repo.delete(updated)
    assert await repo.get(role.id) is None


async def test_role_requires_existing_user_fk(db_session):
    nonexistent_user_id = uuid.uuid4()
    role = Role(user_id=nonexistent_user_id, name="Órfão")
    db_session.add(role)
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_task_repository_filters_by_date_and_status(db_session, test_user: User):
    repo = TaskRepository(db_session)
    await repo.create(user_id=test_user.id, title="Hoje", date=date(2026, 3, 1))
    await repo.create(user_id=test_user.id, title="Outro dia", date=date(2026, 3, 2))
    await repo.create(user_id=test_user.id, title="Concluída", date=date(2026, 3, 1), status=TaskStatus.DONE)

    today_tasks = await repo.list_by_date(test_user.id, date(2026, 3, 1))
    assert len(today_tasks) == 2

    pending = await repo.list_by_status(test_user.id, TaskStatus.PENDING)
    assert len(pending) == 2

    counts = await repo.counts_for_day(test_user.id, date(2026, 3, 1))
    assert counts.get("done") == 1
