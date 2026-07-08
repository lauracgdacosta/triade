"""Quadros e colunas Kanban, personalizáveis por usuário."""

import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin
from app.models.enums import TaskStatus


class KanbanBoard(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "kanban_boards"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False)

    columns: Mapped[list["KanbanColumn"]] = relationship(
        back_populates="board", cascade="all, delete-orphan", order_by="KanbanColumn.position"
    )


class KanbanColumn(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "kanban_columns"

    board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("kanban_boards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#64748b")
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Liga esta coluna a um status de Tarefa: mover o cartão aqui no Kanban
    # atualiza o status da tarefa, e vice-versa (ver TaskService). Colunas
    # customizadas pelo usuário podem ficar sem mapeamento (None) — nesse
    # caso a coluna não participa da sincronia bidirecional.
    maps_to_status: Mapped[TaskStatus | None] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=20), nullable=True
    )

    board: Mapped[KanbanBoard] = relationship(back_populates="columns")


DEFAULT_KANBAN_COLUMNS = [
    {"name": "A Fazer", "color": "#64748b", "status": TaskStatus.PENDING},
    {"name": "Em Andamento", "color": "#0ea5e9", "status": TaskStatus.IN_PROGRESS},
    {"name": "Aguardando", "color": "#f59e0b", "status": TaskStatus.WAITING},
    {"name": "Concluído", "color": "#22c55e", "status": TaskStatus.DONE},
    {"name": "Arquivado", "color": "#94a3b8", "status": TaskStatus.ARCHIVED},
]
