"""Sincronização bidirecional entre `Event` e o Google Calendar.

Pull (Google -> Tríade) grava direto via `EventRepository`, nunca via
`EventService` — evita reenviar (push) de volta pro Google o que acabou de
chegar de lá. Push (Tríade -> Google) é chamado explicitamente pela rota da
API depois que `EventService` já persistiu a mudança local (ver
`api/v1/events.py`) — `EventService` continua livre de I/O externo.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import naive_utc
from app.models.event import Event
from app.models.google_calendar_account import GoogleCalendarAccount
from app.repositories.event_repository import EventRepository
from app.services import google_calendar_client as client
from app.services.google_calendar_account_service import GoogleCalendarAccountService

logger = logging.getLogger(__name__)

_FULL_SYNC_PAST_DAYS = 90
_FULL_SYNC_FUTURE_DAYS = 365
_INSUFFICIENT_SCOPE_MSG = "insufficient authentication scopes"


class GoogleCalendarSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.accounts = GoogleCalendarAccountService(db)
        self.events = EventRepository(db)

    # ---------------- Pull (Google -> Tríade) ----------------

    async def pull_all_accounts(self, user_id: uuid.UUID) -> None:
        """Chamado ao abrir /agenda. Falha numa conta não derruba as outras
        nem a página — a Agenda sempre renderiza com o que já tem local."""
        for account in await self.accounts.list_active(user_id):
            try:
                await self.pull_account(account)
            except Exception:
                logger.exception("Falha ao sincronizar a conta Google %s", account.id)

    async def pull_account(self, account: GoogleCalendarAccount, *, _retried: bool = False) -> None:
        access_token = await self.accounts.get_valid_access_token(account)

        try:
            if account.sync_token:
                page = await client.list_events(access_token, account.calendar_id, sync_token=account.sync_token)
            else:
                now = datetime.now(UTC)
                page = await client.list_events(
                    access_token,
                    account.calendar_id,
                    time_min=now - timedelta(days=_FULL_SYNC_PAST_DAYS),
                    time_max=now + timedelta(days=_FULL_SYNC_FUTURE_DAYS),
                )
        except client.GoogleCalendarError as exc:
            if exc.status_code == 410 and not _retried:
                # syncToken expirado — só acontece uma vez por chamada
                # (nunca re-tenta indefinidamente, mesmo se o full sync
                # também vier com 410, o que não deveria acontecer).
                await self.accounts.clear_sync_token(account)
                await self.pull_account(account, _retried=True)
                return
            if exc.status_code == 403 and _INSUFFICIENT_SCOPE_MSG in exc.message.lower():
                # Conta autorizada sem o escopo do Calendar (usuário negou
                # esse escopo específico na tela de consentimento do
                # Google) — sem isso o pull falharia pra sempre, só nos
                # logs, sem a UI nunca oferecer "reconectar".
                await self.accounts.deactivate(account)
            raise

        next_sync_token: str | None = None
        while True:
            for item in page.get("items", []):
                await self._apply_remote_event(account, item)
            # nextSyncToken só existe na ÚLTIMA página — sobrescrever aqui a
            # cada página garante que só o valor final sobrevive.
            next_sync_token = page.get("nextSyncToken", next_sync_token)
            next_page_token = page.get("nextPageToken")
            if not next_page_token:
                break
            page = await client.list_events_page(access_token, account.calendar_id, next_page_token)

        await self.accounts.record_sync(account, sync_token=next_sync_token, synced_at=datetime.now(UTC))

    async def _apply_remote_event(self, account: GoogleCalendarAccount, item: dict) -> None:
        google_event_id = item["id"]
        existing = await self.events.get_by_google_event(account.id, google_event_id)

        if item.get("status") == "cancelled":
            if existing is not None:
                await self.events.delete(existing)
            return

        fields = self._from_google_event(item)
        if existing is not None:
            await self.events.update(existing, **fields)
        else:
            await self.events.create(
                user_id=account.user_id, google_account_id=account.id, google_event_id=google_event_id, **fields
            )

    def _from_google_event(self, item: dict) -> dict:
        start = item.get("start", {})
        end = item.get("end", {})
        all_day = "date" in start

        if all_day:
            start_at = datetime.fromisoformat(start["date"])
            # end.date do Google é EXCLUSIVO (evento de 1 dia único tem
            # start.date=D, end.date=D+1) — sem o -1 dia, todo evento
            # dia-inteiro importado apareceria um dia mais longo do que é.
            end_at = datetime.fromisoformat(end["date"]) - timedelta(days=1)
            if end_at < start_at:
                end_at = start_at
        else:
            start_at = naive_utc(datetime.fromisoformat(start["dateTime"]))
            end_at = naive_utc(datetime.fromisoformat(end["dateTime"]))

        return {
            "title": item.get("summary") or "(sem título)",
            "description": item.get("description"),
            "location": item.get("location"),
            "all_day": all_day,
            "start_at": start_at,
            "end_at": end_at,
            "google_synced_at": datetime.now(UTC),
        }

    # ---------------- Push (Tríade -> Google) ----------------

    async def push_create(self, event: Event) -> Event:
        if not self._should_sync(event):
            return event
        account = await self.accounts.get(event.google_account_id, event.user_id)
        if account is None:
            return event
        access_token = await self.accounts.get_valid_access_token(account)
        remote = await client.insert_event(access_token, account.calendar_id, self._to_google_event(event))
        return await self.events.update(event, google_event_id=remote["id"], google_synced_at=datetime.now(UTC))

    async def push_update(self, event: Event) -> Event:
        if not self._should_sync(event):
            return event
        if event.google_event_id is None:
            return await self.push_create(event)
        account = await self.accounts.get(event.google_account_id, event.user_id)
        if account is None:
            return event
        access_token = await self.accounts.get_valid_access_token(account)
        await client.update_event(access_token, account.calendar_id, event.google_event_id, self._to_google_event(event))
        return await self.events.update(event, google_synced_at=datetime.now(UTC))

    async def push_delete(self, event: Event) -> None:
        if event.google_account_id is None or event.google_event_id is None:
            return
        account = await self.accounts.get(event.google_account_id, event.user_id)
        if account is None:
            return
        access_token = await self.accounts.get_valid_access_token(account)
        await client.delete_event(access_token, account.calendar_id, event.google_event_id)

    def _should_sync(self, event: Event) -> bool:
        # Compromissos recorrentes (RRULE) não sincronizam por enquanto —
        # reconciliar recorrência nos dois sentidos é bem mais complexo
        # (edição de instância única vs série inteira) e ficou fora do
        # escopo atual; a validação em EventCreate/EventUpdate já deveria
        # impedir essa combinação antes de chegar aqui, isto é só uma
        # segunda trava silenciosa.
        return event.google_account_id is not None and not event.recurrence_rule

    def _to_google_event(self, event: Event) -> dict:
        if event.all_day:
            body_start = {"date": event.start_at.date().isoformat()}
            body_end = {"date": (event.end_at.date() + timedelta(days=1)).isoformat()}
        else:
            # timeZone explícito é obrigatório: sem ele o Google assume o
            # timezone padrão do calendário do usuário, deslocando o
            # horário silenciosamente (Event.start_at/end_at já são UTC).
            body_start = {"dateTime": event.start_at.isoformat() + "Z", "timeZone": "UTC"}
            body_end = {"dateTime": event.end_at.isoformat() + "Z", "timeZone": "UTC"}

        body: dict = {"summary": event.title, "start": body_start, "end": body_end}
        if event.description:
            body["description"] = event.description
        if event.location:
            body["location"] = event.location
        return body
