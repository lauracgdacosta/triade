"""Testes do SearchService: busca multi-entidade e filtros aplicados a tarefas."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.models.enums import Priority
from app.models.user import User
from app.schemas.event import EventCreate
from app.schemas.goal import GoalCreate
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.services.event_service import EventService
from app.services.goal_service import GoalService
from app.services.project_service import ProjectService
from app.services.search_service import SearchService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_search_finds_matches_across_entities(db_session, test_user: User):
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Revisar orçamento"))
    await ProjectService(db_session).create(test_user.id, ProjectCreate(name="Orçamento anual"))
    await GoalService(db_session).create(test_user.id, GoalCreate(title="Fechar orçamento Q3"))
    start = datetime.now(UTC) + timedelta(days=1)
    await EventService(db_session).create(
        test_user.id,
        EventCreate(title="Reunião de orçamento", start_at=start, end_at=start + timedelta(hours=1)),
    )

    response = await SearchService(db_session).search(test_user.id, "orçamento")

    assert response.total == 4
    types = {r.entity_type for r in response.results}
    assert types == {"task", "project", "goal", "event"}


async def test_search_ignores_non_matching(db_session, test_user: User):
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Comprar leite"))

    response = await SearchService(db_session).search(test_user.id, "orçamento")
    assert response.total == 0


async def test_search_filters_tasks_by_priority(db_session, test_user: User):
    await TaskService(db_session).create(
        test_user.id, TaskCreate(title="Tarefa urgente", priority=Priority.URGENT)
    )
    await TaskService(db_session).create(
        test_user.id, TaskCreate(title="Tarefa normal", priority=Priority.NONE)
    )

    response = await SearchService(db_session).search(test_user.id, "Tarefa", priority=Priority.URGENT)
    assert response.total == 1
    assert response.results[0].title == "Tarefa urgente"


async def test_search_filters_tasks_by_date_range(db_session, test_user: User):
    today = date.today()
    await TaskService(db_session).create(test_user.id, TaskCreate(title="Tarefa hoje", date=today))
    await TaskService(db_session).create(
        test_user.id, TaskCreate(title="Tarefa futura", date=today + timedelta(days=10))
    )

    response = await SearchService(db_session).search(
        test_user.id, "Tarefa", date_from=today, date_to=today + timedelta(days=2)
    )
    assert response.total == 1
    assert response.results[0].title == "Tarefa hoje"
