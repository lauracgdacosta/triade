"""Endpoints JSON de Tarefas: CRUD + ações (duplicar/arquivar/concluir/cancelar/reabrir)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.enums import TaskStatus
from app.models.user import User
from app.schemas.attachment import AttachmentRead
from app.schemas.task import KanbanMoveRequest, TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_owned_task(task_id: uuid.UUID, user: User, service: TaskService):
    task = await service.get(task_id, user.id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada.")
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    date_from: date | None = None,
    date_to: date | None = None,
    status_filter: TaskStatus | None = None,
    q: str | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    if q:
        return await service.search(user.id, q)
    if status_filter:
        return await service.list_by_status(user.id, status_filter)
    if date_from and date_to:
        return await service.list_between(user.id, date_from, date_to)
    if date_from:
        return await service.list_by_date(user.id, date_from)
    return await service.list_between(user.id, date.min, date.max)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    return await TaskService(db).create(user.id, payload)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    return await _get_owned_task(task_id, user, service)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.update(task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    await service.delete(task)


@router.post("/{task_id}/duplicate", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def duplicate_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.duplicate(task)


@router.post("/{task_id}/archive", response_model=TaskRead)
async def archive_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.archive(task)


@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.complete(task)


@router.post("/{task_id}/cancel", response_model=TaskRead)
async def cancel_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.cancel(task)


@router.post("/{task_id}/reopen", response_model=TaskRead)
async def reopen_task(
    task_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.reopen(task)


@router.post("/{task_id}/kanban-move", response_model=TaskRead)
async def move_task_kanban(
    task_id: uuid.UUID,
    payload: KanbanMoveRequest,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    return await service.move_to_kanban(task, payload.kanban_column_id, payload.position)


@router.post("/{task_id}/attachments", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    content = await file.read()
    return await service.add_attachment(
        task, file.filename or "anexo", content, file.content_type or "application/octet-stream"
    )


@router.delete("/{task_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    task_id: uuid.UUID,
    attachment_id: uuid.UUID,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await _get_owned_task(task_id, user, service)
    attachment = next((a for a in task.attachments if a.id == attachment_id), None)
    if attachment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Anexo não encontrado.")
    await service.remove_attachment(attachment)
