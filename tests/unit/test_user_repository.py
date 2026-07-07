"""Testes do UserRepository: provisionamento automático no primeiro login."""

import uuid

import pytest

from app.repositories.kanban_repository import KanbanBoardRepository
from app.repositories.user_repository import UserRepository

pytestmark = pytest.mark.asyncio


async def test_get_or_create_provisions_settings_and_kanban_board(db_session):
    repo = UserRepository(db_session)
    user_id = uuid.uuid4()

    user = await repo.get_or_create(user_id=user_id, email="novo@example.com")
    assert user.email == "novo@example.com"

    board = await KanbanBoardRepository(db_session).get_default_for_user(user_id)
    assert board is not None
    assert len(board.columns) == 5


async def test_get_or_create_is_idempotent(db_session):
    repo = UserRepository(db_session)
    user_id = uuid.uuid4()

    first = await repo.get_or_create(user_id=user_id, email="mesmo@example.com")
    second = await repo.get_or_create(user_id=user_id, email="mesmo@example.com")
    assert first.id == second.id

    boards = await KanbanBoardRepository(db_session).list_for_user(user_id)
    assert len(boards) == 1
