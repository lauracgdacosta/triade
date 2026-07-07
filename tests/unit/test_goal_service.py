"""Testes do GoalService: progresso calculado a partir das tarefas vinculadas."""

import pytest

from app.models.user import User
from app.schemas.goal import GoalCreate, GoalUpdate
from app.schemas.task import TaskCreate
from app.services.goal_service import GoalService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_goal_progress_with_no_tasks(db_session, test_user: User):
    service = GoalService(db_session)
    goal = await service.create(test_user.id, GoalCreate(title="Aprender FastAPI"))
    read = await service.get_read(goal.id, test_user.id)
    assert read.tasks_done == 0
    assert read.tasks_total == 0


async def test_goal_progress_reflects_linked_tasks(db_session, test_user: User):
    goal_service = GoalService(db_session)
    task_service = TaskService(db_session)

    goal = await goal_service.create(test_user.id, GoalCreate(title="Meta com tarefas"))
    t1 = await task_service.create(test_user.id, TaskCreate(title="Passo 1", goal_id=goal.id))
    await task_service.create(test_user.id, TaskCreate(title="Passo 2", goal_id=goal.id))
    await task_service.complete(t1)

    read = await goal_service.get_read(goal.id, test_user.id)
    assert read.tasks_total == 2
    assert read.tasks_done == 1


async def test_goal_update_percent_complete(db_session, test_user: User):
    service = GoalService(db_session)
    goal = await service.create(test_user.id, GoalCreate(title="Atualizar"))
    updated = await service.update(goal, GoalUpdate(percent_complete=75))
    assert float(updated.percent_complete) == 75.0
