"""Persistência de Quadros e Colunas Kanban."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.kanban import KanbanBoard, KanbanColumn
from app.repositories.base import BaseRepository


class KanbanBoardRepository(BaseRepository[KanbanBoard]):
    model = KanbanBoard

    async def get_default_for_user(self, user_id: uuid.UUID) -> KanbanBoard | None:
        stmt = (
            select(KanbanBoard)
            .options(selectinload(KanbanBoard.columns))
            .where(KanbanBoard.user_id == user_id, KanbanBoard.is_default.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class KanbanColumnRepository(BaseRepository[KanbanColumn]):
    model = KanbanColumn

    async def list_for_board(self, board_id: uuid.UUID) -> list[KanbanColumn]:
        stmt = select(KanbanColumn).where(KanbanColumn.board_id == board_id).order_by(
            KanbanColumn.position
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
