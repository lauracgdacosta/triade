"""Testes do TaskService: CRUD e ações (duplicar/arquivar/concluir/cancelar/reabrir)."""

import pytest

from app.models.enums import Priority, TaskStatus
from app.models.user import User
from app.repositories.kanban_repository import KanbanBoardRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService

pytestmark = pytest.mark.asyncio


async def test_create_task(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Nova tarefa", priority=Priority.URGENT))
    assert task.title == "Nova tarefa"
    assert task.priority == Priority.URGENT
    assert task.status == TaskStatus.PENDING


async def test_create_task_lands_in_first_kanban_column(db_session, test_user: User):
    """Regressão: sem isso, kanban_column_id ficava None e a tarefa nunca
    aparecia em nenhuma coluna do Kanban — não tem como arrastar um cartão
    que nunca chega a ser exibido, então o quadro parecia sempre quebrado/vazio."""
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Vai pro Kanban"))
    assert task.kanban_column_id is not None

    from app.repositories.kanban_repository import KanbanBoardRepository

    board = await KanbanBoardRepository(db_session).get_default_for_user(test_user.id)
    assert task.kanban_column_id == board.columns[0].id


async def test_duplicate_preserves_kanban_column(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Original"))
    clone = await service.duplicate(task)
    assert clone.kanban_column_id == task.kanban_column_id


async def test_update_task_partial(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Original"))
    updated = await service.update(task, TaskUpdate(title="Atualizada"))
    assert updated.title == "Atualizada"


async def test_complete_sets_status_and_timestamp(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="A concluir"))
    completed = await service.complete(task)
    assert completed.status == TaskStatus.DONE
    assert completed.completed_at is not None


async def test_reopen_clears_completed_at(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Reabrir"))
    await service.complete(task)
    reopened = await service.reopen(task)
    assert reopened.status == TaskStatus.PENDING
    assert reopened.completed_at is None


async def test_cancel_and_archive(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Cancelar"))
    cancelled = await service.cancel(task)
    assert cancelled.status == TaskStatus.CANCELLED

    task2 = await service.create(test_user.id, TaskCreate(title="Arquivar"))
    archived = await service.archive(task2)
    assert archived.status == TaskStatus.ARCHIVED


async def test_wait(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Aguardando"))
    waiting = await service.wait(task)
    assert waiting.status == TaskStatus.WAITING


async def test_status_actions_move_kanban_column(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Sincronizar com o kanban"))

    board = await KanbanBoardRepository(db_session).get_default_for_user(test_user.id)
    columns_by_name = {c.name: c for c in board.columns}

    started = await service.start(task)
    assert started.status == TaskStatus.IN_PROGRESS
    assert started.kanban_column_id == columns_by_name["Em Andamento"].id

    waiting = await service.wait(task)
    assert waiting.status == TaskStatus.WAITING
    assert waiting.kanban_column_id == columns_by_name["Aguardando"].id

    completed = await service.complete(task)
    assert completed.status == TaskStatus.DONE
    assert completed.kanban_column_id == columns_by_name["Concluído"].id
    assert completed.completed_at is not None


async def test_move_to_kanban_updates_status(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Arrastar no kanban"))

    board = await KanbanBoardRepository(db_session).get_default_for_user(test_user.id)
    done_column = next(c for c in board.columns if c.name == "Concluído")

    moved = await service.move_to_kanban(task, done_column.id, 0)
    assert moved.status == TaskStatus.DONE
    assert moved.completed_at is not None


async def test_duplicate_creates_copy(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Original", priority=Priority.IMPORTANT))
    clone = await service.duplicate(task)
    assert clone.id != task.id
    assert clone.title == "Original (cópia)"
    assert clone.priority == Priority.IMPORTANT


async def test_search_by_title(db_session, test_user: User):
    service = TaskService(db_session)
    await service.create(test_user.id, TaskCreate(title="Relatório mensal"))
    await service.create(test_user.id, TaskCreate(title="Outra coisa"))
    results = await service.search(test_user.id, "relatório")
    assert len(results) == 1
    assert results[0].title == "Relatório mensal"


async def test_list_by_status(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Pendente"))
    await service.complete(task)
    await service.create(test_user.id, TaskCreate(title="Outra pendente"))

    pending = await service.list_by_status(test_user.id, TaskStatus.PENDING)
    done = await service.list_by_status(test_user.id, TaskStatus.DONE)
    assert len(pending) == 1
    assert len(done) == 1
