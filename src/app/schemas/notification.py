"""Schemas de Notificações."""

import datetime as dt
import uuid

from app.models.enums import NotificationType
from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: uuid.UUID
    type: NotificationType
    title: str
    message: str | None
    read: bool
    created_at: dt.datetime
