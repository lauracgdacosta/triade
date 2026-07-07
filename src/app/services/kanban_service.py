"""Regra de negócio do Kanban: quadro padrão, colunas customizáveis e movimentação."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kanban import KanbanBoard, KanbanColumn
from app.repositories.kanban_repository import KanbanBoardRepository, KanbanColumnRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.kanban import KanbanColumnCreate, KanbanColumnUpdate


class KanbanService:
    def __init__(self, db: AsyncSession):
        self.board_repo = KanbanBoardRepository(db)
        self.column_repo = KanbanColumnRepository(db)
        self.task_repo = TaskRepository(db)

    async def get_board(self, user_id: uuid.UUID) -> KanbanBoard | None:
        return await self.board_repo.get_default_for_user(user_id)

    async def board_with_tasks(self, user_id: uuid.UUID) -> tuple[KanbanBoard, dict[uuid.UUID, list]]:
        board = await self.get_board(user_id)
        tasks_by_column = {}
        for column in board.columns:
            tasks_by_column[column.id] = await self.task_repo.list_by_kanban_column(user_id, column.id)
        return board, tasks_by_column

    async def add_column(self, board: KanbanBoard, data: KanbanColumnCreate) -> KanbanColumn:
        position = len(board.columns)
        return await self.column_repo.create(
            board_id=board.id, position=position, **data.model_dump()
        )

    async def update_column(self, column: KanbanColumn, data: KanbanColumnUpdate) -> KanbanColumn:
        return await self.column_repo.update(column, **data.model_dump(exclude_unset=True))

    async def delete_column(self, column: KanbanColumn) -> None:
        await self.column_repo.delete(column)
