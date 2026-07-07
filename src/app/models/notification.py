"""Notificações do usuário. Schema pronto — motor de disparo/UI na Rodada 2."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base
from app.models.base import TimestampMixin, UUIDPkMixin, naive_utc
from app.models.enums import NotificationType


class Notification(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False, length=30), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column()

    @validates("scheduled_for")
    def _validate_scheduled_for(self, _key: str, value: datetime | None) -> datetime | None:
        return naive_utc(value)
