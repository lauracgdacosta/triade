"""Testes do KanbanService: quadro padrão seedado no primeiro login e movimentação."""

import pytest

from app.models.user import User
from app.schemas.kanban import KanbanColumnCreate
from app.schemas.task import TaskCreate
from app.services.kanban_service import KanbanService
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_default_board_seeded_for_new_user(db_session, test_user: User):
    service = KanbanService(db_session)
    board = await service.get_board(test_user.id)
    assert board is not None
    assert board.is_default is True
    names = [c.name for c in board.columns]
    assert names == ["A Fazer", "Em Andamento", "Aguardando", "Concluído", "Arquivado"]


async def test_add_custom_column(db_session, test_user: User):
    service = KanbanService(db_session)
    board = await service.get_board(test_user.id)
    column = await service.add_column(board, KanbanColumnCreate(name="Revisão", color="#111111"))
    assert column.position == 5
    assert column.name == "Revisão"


async def test_move_task_between_columns(db_session, test_user: User):
    kanban_service = KanbanService(db_session)
    task_service = TaskService(db_session)
    board = await kanban_service.get_board(test_user.id)
    target_column = board.columns[1]

    task = await task_service.create(test_user.id, TaskCreate(title="Mover"))
    moved = await task_service.move_to_kanban(task, target_column.id, 0)
    assert moved.kanban_column_id == target_column.id

    _, tasks_by_column = await kanban_service.board_with_tasks(test_user.id)
    assert len(tasks_by_column[target_column.id]) == 1
