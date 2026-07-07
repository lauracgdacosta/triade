"""Regra de negócio das preferências (Settings) do usuário."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import UserSettings
from app.repositories.settings_repository import SettingsRepository
from app.schemas.user import SettingsUpdate


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.repo = SettingsRepository(db)

    async def get(self, user_id: uuid.UUID) -> UserSettings | None:
        return await self.repo.get(user_id)

    async def update(self, settings: UserSettings, data: SettingsUpdate) -> UserSettings:
        return await self.repo.update(settings, **data.model_dump(exclude_unset=True))
