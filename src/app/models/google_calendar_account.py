"""Contas Google conectadas para sincronização bidirecional com a Agenda."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin


class GoogleCalendarAccount(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "google_calendar_accounts"
    __table_args__ = (UniqueConstraint("user_id", "google_sub", name="uq_google_calendar_accounts_user_sub"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    google_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary")

    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scope: Mapped[str] = mapped_column(String(255), nullable=False)

    # NULL = nunca sincronizado ainda (força full sync na próxima vez).
    sync_token: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # False quando o refresh_token vira inválido (revogado pelo usuário direto
    # no Google) — a linha não é apagada, só marcada, para a UI oferecer
    # "reconectar" em vez de simplesmente sumir com o histórico de sync.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
