"""Testes do TaskService: CRUD e ações (duplicar/arquivar/concluir/cancelar/reabrir)."""

from datetime import date, datetime, time

import pytest

from app.models.enums import Priority, TaskStatus
from app.models.user import User
from app.repositories.event_repository import EventRepository
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


async def test_create_recurring_defaults_date_to_today(db_session, test_user: User):
    service = TaskService(db_session)
    task = await service.create(test_user.id, TaskCreate(title="Checar email", is_recurring=True))
    assert task.is_recurring is True
    assert task.date == date.today()


async def test_ensure_recurring_occurrences_creates_only_missing_days(db_session, test_user: User):
    service = TaskService(db_session)
    template = await service.create(
        test_user.id, TaskCreate(title="Checar email", is_recurring=True, date=date(2026, 1, 1))
    )

    # No mesmo dia do template: nada a gerar.
    await service.ensure_recurring_occurrences(test_user.id, today=date(2026, 1, 1))
    all_tasks = await service.list_between(test_user.id, date(2026, 1, 1), date(2026, 1, 1))
    assert len(all_tasks) == 1

    # Dia seguinte: gera exatamente uma ocorrência nova.
    await service.ensure_recurring_occurrences(test_user.id, today=date(2026, 1, 2))
    occurrence = (await service.list_by_date(test_user.id, date(2026, 1, 2)))[0]
    assert occurrence.recurring_parent_id == template.id
    assert occurrence.title == template.title
    assert occurrence.is_recurring is False
    assert occurrence.status == TaskStatus.PENDING

    # Rodar de novo no mesmo dia não duplica.
    await service.ensure_recurring_occurrences(test_user.id, today=date(2026, 1, 2))
    assert len(await service.list_by_date(test_user.id, date(2026, 1, 2))) == 1


async def test_stop_recurrence_from_child_stops_future_generation(db_session, test_user: User):
    service = TaskService(db_session)
    template = await service.create(
        test_user.id, TaskCreate(title="Checar email", is_recurring=True, date=date(2026, 1, 1))
    )
    await service.ensure_recurring_occurrences(test_user.id, today=date(2026, 1, 2))
    child = (await service.list_by_date(test_user.id, date(2026, 1, 2)))[0]

    await service.stop_recurrence(child)

    await service.ensure_recurring_occurrences(test_user.id, today=date(2026, 1, 3))
    assert await service.list_by_date(test_user.id, date(2026, 1, 3)) == []
    refreshed_template = await service.get(template.id, test_user.id)
    assert refreshed_template.is_recurring is False


async def test_create_with_kanban_column_id_uses_given_column_and_status(db_session, test_user: User):
    service = TaskService(db_session)
    board = await KanbanBoardRepository(db_session).get_default_for_user(test_user.id)
    done_column = next(c for c in board.columns if c.maps_to_status == TaskStatus.DONE)
    task = await service.create(
        test_user.id, TaskCreate(title="Direto pro Concluído", kanban_column_id=done_column.id)
    )
    assert task.kanban_column_id == done_column.id
    assert task.status == TaskStatus.DONE


async def test_sync_from_event_creates_linked_task_with_local_date_time(db_session, test_user: User):
    # test_user.timezone é "America/Sao_Paulo" (padrão do modelo) = UTC-3
    # (sem horário de verão desde 2019) — 09:00 UTC deve virar 06:00 local.
    event = await EventRepository(db_session).create(
        user_id=test_user.id,
        title="Reunião",
        start_at=datetime(2026, 1, 10, 9),
        end_at=datetime(2026, 1, 10, 10),
        all_day=False,
        location="Sala 1",
        meeting_link="https://meet.google.com/abc-defg-hij",
    )
    task = await TaskService(db_session).sync_from_event(event)
    assert task is not None
    assert task.source_event_id == event.id
    assert task.title == "Reunião"
    assert task.location == "Sala 1"
    assert task.meeting_link == "https://meet.google.com/abc-defg-hij"
    assert task.date == date(2026, 1, 10)
    assert task.time == time(6, 0)
    assert task.kanban_column_id is not None


async def test_sync_from_event_skips_all_day_event(db_session, test_user: User):
    event = await EventRepository(db_session).create(
        user_id=test_user.id, title="Feriado", start_at=datetime(2026, 1, 10), end_at=datetime(2026, 1, 10), all_day=True
    )
    task = await TaskService(db_session).sync_from_event(event)
    assert task is None


async def test_sync_from_event_updates_existing_linked_task_without_duplicating(db_session, test_user: User):
    event = await EventRepository(db_session).create(
        user_id=test_user.id, title="Original", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10), all_day=False
    )
    service = TaskService(db_session)
    first = await service.sync_from_event(event)

    event = await EventRepository(db_session).update(event, title="Renomeado")
    second = await service.sync_from_event(event)

    assert second.id == first.id
    assert second.title == "Renomeado"
    assert len(await service.list_by_status(test_user.id, TaskStatus.PENDING)) == 1


async def test_sync_from_event_removes_task_when_event_becomes_all_day(db_session, test_user: User):
    event = await EventRepository(db_session).create(
        user_id=test_user.id, title="Vira dia-inteiro", start_at=datetime(2026, 1, 10, 9), end_at=datetime(2026, 1, 10, 10), all_day=False
    )
    service = TaskService(db_session)
    task = await service.sync_from_event(event)

    event = await EventRepository(db_session).update(event, all_day=True)
    result = await service.sync_from_event(event)

    assert result is None
    assert await service.repo.get(task.id) is None


async def test_sync_from_event_sanitizes_description(db_session, test_user: User):
    event = await EventRepository(db_session).create(
        user_id=test_user.id,
        title="Com script malicioso",
        description="<script>alert(1)</script>texto normal",
        start_at=datetime(2026, 1, 10, 9),
        end_at=datetime(2026, 1, 10, 10),
        all_day=False,
    )
    task = await TaskService(db_session).sync_from_event(event)
    assert "<script>" not in task.description
