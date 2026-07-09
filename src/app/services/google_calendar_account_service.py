"""Regra de negócio das contas Google conectadas: OAuth, refresh e desconexão.

Ponto único de criptografia/decriptação e de renovação de token — quem
precisa falar com a Calendar API (push e pull) sempre passa por
`get_valid_access_token`, nunca lê `access_token_encrypted` diretamente.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.google_calendar_account import GoogleCalendarAccount
from app.repositories.google_calendar_account_repository import GoogleCalendarAccountRepository
from app.services import google_calendar_client as client
from app.utils import crypto

_EXPIRY_LEEWAY_SECONDS = 60


def _as_aware_utc(value: datetime) -> datetime:
    """SQLite (usado localmente/testes) não preserva tzinfo em colunas
    `DateTime(timezone=True)` no round-trip — ao contrário do Postgres real.
    Sem isso, comparar `token_expires_at` com `datetime.now(UTC)` quebra só
    localmente com `TypeError: can't compare offset-naive and offset-aware`."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class GoogleCalendarAccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GoogleCalendarAccountRepository(db)

    async def list(self, user_id: uuid.UUID) -> list[GoogleCalendarAccount]:
        """Todas as contas (ativas e inativas) — a UI mostra "reconexão
        necessária" para as inativas em vez de escondê-las."""
        return await self.repo.list_for_user(user_id)

    async def list_active(self, user_id: uuid.UUID) -> list[GoogleCalendarAccount]:
        return await self.repo.list_active_for_user(user_id)

    async def get(self, account_id: uuid.UUID, user_id: uuid.UUID) -> GoogleCalendarAccount | None:
        account = await self.repo.get(account_id)
        if account is None or account.user_id != user_id:
            return None
        return account

    async def create_from_oauth(
        self,
        user_id: uuid.UUID,
        *,
        google_sub: str,
        email: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: str,
    ) -> GoogleCalendarAccount:
        """Cria a conta ou reativa uma existente (upsert por user_id+google_sub —
        reconectar após revogar/desconectar não duplica a linha)."""
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        existing = await self.repo.get_by_sub_for_user(user_id, google_sub)
        if existing is not None:
            return await self.repo.update(
                existing,
                email=email,
                access_token_encrypted=crypto.encrypt(access_token),
                refresh_token_encrypted=crypto.encrypt(refresh_token),
                token_expires_at=expires_at,
                scope=scope,
                is_active=True,
            )
        return await self.repo.create(
            user_id=user_id,
            google_sub=google_sub,
            email=email,
            access_token_encrypted=crypto.encrypt(access_token),
            refresh_token_encrypted=crypto.encrypt(refresh_token),
            token_expires_at=expires_at,
            scope=scope,
        )

    async def update_tokens(
        self, account: GoogleCalendarAccount, *, access_token: str, expires_in: int, refresh_token: str | None = None
    ) -> GoogleCalendarAccount:
        updates: dict = {
            "access_token_encrypted": crypto.encrypt(access_token),
            "token_expires_at": datetime.now(UTC) + timedelta(seconds=expires_in),
        }
        if refresh_token:
            updates["refresh_token_encrypted"] = crypto.encrypt(refresh_token)
        return await self.repo.update(account, **updates)

    async def get_valid_access_token(self, account: GoogleCalendarAccount) -> str:
        expires_at = _as_aware_utc(account.token_expires_at)
        if expires_at > datetime.now(UTC) + timedelta(seconds=_EXPIRY_LEEWAY_SECONDS):
            return crypto.decrypt(account.access_token_encrypted)

        refresh_token = crypto.decrypt(account.refresh_token_encrypted)
        try:
            tokens = await client.refresh_access_token(refresh_token)
        except client.GoogleCalendarError as exc:
            # 400 no refresh quase sempre significa invalid_grant (usuário
            # revogou o acesso direto no Google) — marca a conta pra UI
            # oferecer reconexão em vez de falhar silenciosamente sempre.
            if exc.status_code == 400:
                await self.deactivate(account)
            raise

        await self.update_tokens(account, access_token=tokens["access_token"], expires_in=tokens.get("expires_in", 3600))
        return tokens["access_token"]

    async def record_sync(
        self, account: GoogleCalendarAccount, *, sync_token: str | None, synced_at: datetime
    ) -> GoogleCalendarAccount:
        """Persiste o resultado de um pull (ver GoogleCalendarSyncService).
        `sync_token=None` só é gravado explicitamente quando o full sync não
        devolveu nenhum (raro) — nunca sobrescreve um token válido por engano."""
        updates: dict = {"last_synced_at": synced_at}
        if sync_token:
            updates["sync_token"] = sync_token
        return await self.repo.update(account, **updates)

    async def clear_sync_token(self, account: GoogleCalendarAccount) -> GoogleCalendarAccount:
        """Força full sync na próxima vez (ex.: syncToken expirou, 410 Gone)."""
        return await self.repo.update(account, sync_token=None)

    async def deactivate(self, account: GoogleCalendarAccount) -> GoogleCalendarAccount:
        return await self.repo.update(account, is_active=False)

    async def disconnect(self, account: GoogleCalendarAccount) -> None:
        """Remove a conta. Os eventos locais vinculados não são apagados —
        só perdem o vínculo (viram eventos comuns de novo)."""
        stmt = (
            update(Event)
            .where(Event.google_account_id == account.id)
            .values(google_account_id=None, google_event_id=None, google_synced_at=None)
        )
        await self.db.execute(stmt)
        await self.repo.delete(account)
