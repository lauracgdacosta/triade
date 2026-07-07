"""Persistência das preferências (Settings) do usuário."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import UserSettings


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID) -> UserSettings | None:
        return await self.session.get(UserSettings, user_id)

    async def update(self, settings: UserSettings, **kwargs: object) -> UserSettings:
        for key, value in kwargs.items():
            setattr(settings, key, value)
        await self.session.flush()
        await self.session.refresh(settings)
        return settings
