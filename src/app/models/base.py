"""Mixins compartilhados pelos models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


def naive_utc(value: datetime | None) -> datetime | None:
    """Normaliza para *naive* (sem tzinfo) um datetime que vai para uma coluna
    `timestamp without time zone` (ex.: `Event.start_at`, `Task.completed_at`,
    `PomodoroSession.started_at`, `TimeEntry.start_at`).

    Sem isso, gravar ou comparar um datetime timezone-aware (ex.: vindo de
    `datetime.now(UTC)` no backend, ou de `.toISOString()` no front-end via
    FullCalendar) contra essas colunas quebra no asyncpg em runtime — SQLite
    não distingue os dois casos, então o bug só aparece contra o Postgres
    real. Se o valor tiver um offset diferente de UTC, converte antes de
    descartar o tzinfo (em vez de simplesmente truncar, o que preservaria o
    horário errado).
    """
    if value is not None and value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


class UUIDPkMixin:
    """Chave primária UUID, compatível com Postgres (Supabase) e SQLite (testes)."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Colunas de auditoria de criação/atualização."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
