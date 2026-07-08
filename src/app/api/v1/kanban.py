"""Endpoints JSON do Kanban: quadro padrão, colunas customizáveis."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.kanban import (
    KanbanBoardRead,
    KanbanColumnCreate,
    KanbanColumnRead,
    KanbanColumnUpdate,
)
from app.services.kanban_service import KanbanService

router = APIRouter(prefix="/kanban", tags=["kanban"])


@router.get("/board", response_model=KanbanBoardRead)
async def get_board(user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)):
    service = KanbanService(db)
    board, tasks_by_column = await service.board_with_tasks(user.id)
    columns = []
    for column in board.columns:
        columns.append(
            KanbanColumnRead(
                id=column.id,
                name=column.name,
                color=column.color,
                position=column.position,
                maps_to_status=column.maps_to_status,
                tasks=tasks_by_column.get(column.id, []),
            )
        )
    return KanbanBoardRead(id=board.id, name=board.name, is_default=board.is_default, columns=columns)


@router.post("/columns", response_model=KanbanColumnRead, status_code=status.HTTP_201_CREATED)
async def create_column(
    payload: KanbanColumnCreate, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = KanbanService(db)
    board = await service.get_board(user.id)
    column = await service.add_column(board, payload)
    return KanbanColumnRead(
        id=column.id, name=column.name, color=column.color, position=column.position,
        maps_to_status=column.maps_to_status,
    )


@router.patch("/columns/{column_id}", response_model=KanbanColumnRead)
async def update_column(
    column_id: uuid.UUID,
    payload: KanbanColumnUpdate,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = KanbanService(db)
    board = await service.get_board(user.id)
    column = next((c for c in board.columns if c.id == column_id), None)
    if column is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Coluna não encontrada.")
    column = await service.update_column(column, payload)
    return KanbanColumnRead(
        id=column.id, name=column.name, color=column.color, position=column.position,
        maps_to_status=column.maps_to_status,
    )


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: uuid.UUID, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    service = KanbanService(db)
    board = await service.get_board(user.id)
    column = next((c for c in board.columns if c.id == column_id), None)
    if column is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Coluna não encontrada.")
    await service.delete_column(column)
