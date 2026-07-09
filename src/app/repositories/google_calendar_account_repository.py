"""Persistência de contas Google conectadas."""

import uuid

from sqlalchemy import select

from app.models.google_calendar_account import GoogleCalendarAccount
from app.repositories.base import BaseRepository


class GoogleCalendarAccountRepository(BaseRepository[GoogleCalendarAccount]):
    model = GoogleCalendarAccount

    async def get_by_sub_for_user(self, user_id: uuid.UUID, google_sub: str) -> GoogleCalendarAccount | None:
        stmt = select(GoogleCalendarAccount).where(
            GoogleCalendarAccount.user_id == user_id, GoogleCalendarAccount.google_sub == google_sub
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_for_user(self, user_id: uuid.UUID) -> list[GoogleCalendarAccount]:
        stmt = select(GoogleCalendarAccount).where(
            GoogleCalendarAccount.user_id == user_id, GoogleCalendarAccount.is_active.is_(True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
