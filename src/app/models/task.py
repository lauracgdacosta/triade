"""Tarefa: entidade central do sistema."""

import datetime as dt
import uuid

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin, naive_utc
from app.models.enums import Priority, TaskStatus
from app.models.tag import Tag, task_tags


class Task(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)  # HTML/markdown rico
    notes: Mapped[str | None] = mapped_column(Text)

    date: Mapped[dt.date | None] = mapped_column(Date, index=True, nullable=True)
    time: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    planned_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    actual_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)

    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, native_enum=False, length=20), default=Priority.NONE, index=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=20), default=TaskStatus.PENDING, index=True
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), index=True
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), index=True
    )
    kanban_column_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("kanban_columns.id", ondelete="SET NULL"), index=True
    )
    kanban_position: Mapped[int] = mapped_column(Integer, default=0)

    # Recorrência diária: `is_recurring` marca a tarefa "modelo" (a partir da
    # qual novas ocorrências são geradas); `recurring_parent_id` liga cada
    # ocorrência gerada de volta ao modelo que a originou. Ver
    # TaskService.ensure_recurring_occurrences.
    is_recurring: Mapped[bool] = mapped_column(default=False)
    recurring_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )

    color: Mapped[str | None] = mapped_column(String(20))
    location: Mapped[str | None] = mapped_column(String(255))
    meeting_link: Mapped[str | None] = mapped_column(String(500))

    # Vínculo com o compromisso da Agenda que gerou esta tarefa (ver
    # TaskService.sync_from_event) — NULL = tarefa criada diretamente pelo
    # usuário, nunca ligada a um evento. ON DELETE CASCADE: apagar o evento
    # apaga a tarefa vinculada automaticamente, sem código extra nos
    # caminhos de delete de Event (local ou sync do Google).
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), index=True
    )

    completed_at: Mapped[dt.datetime | None] = mapped_column()

    @validates("completed_at")
    def _validate_completed_at(self, _key: str, value: dt.datetime | None) -> dt.datetime | None:
        return naive_utc(value)

    tags: Mapped[list[Tag]] = relationship(secondary=task_tags, lazy="selectin")
    attachments: Mapped[list["Attachment"]] = relationship(  # noqa: F821
        back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )
