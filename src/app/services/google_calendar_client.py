"""Cliente HTTP fino para OAuth2 e a API REST do Google Calendar (v3).

Mesmo estilo de `app/auth/supabase_client.py`: funções livres, uma exceção
customizada, sem SDK oficial (o projeto prefere HTTP fino a bibliotecas
pesadas). Este módulo só fala HTTP puro — a tradução entre o schema `Event`
do Tríade e o corpo de evento do Google mora em `GoogleCalendarSyncService`.
"""

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import get_settings

settings = get_settings()

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"
# openid+email são exigidos pelo endpoint /oauth2/v3/userinfo (usado logo
# após o exchange pra descobrir a conta conectada) — sem eles o token só
# tem acesso à Calendar API e a chamada de userinfo falha com 401/403.
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"
_SCOPE = f"openid email {CALENDAR_SCOPE}"


class GoogleCalendarError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _handle_error(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    try:
        body = response.json()
    except ValueError:
        raise GoogleCalendarError(response.text, response.status_code) from None

    # Dois formatos de erro coexistem: o endpoint OAuth2 de token usa
    # {"error": "invalid_grant", "error_description": "..."} (string), a
    # Calendar API usa {"error": {"code":..., "message": "..."}} (aninhado).
    error = body.get("error")
    if isinstance(error, dict):
        detail = error.get("message") or response.text
    else:
        detail = body.get("error_description") or error or response.text
    raise GoogleCalendarError(detail, response.status_code)


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _events_url(calendar_id: str, suffix: str = "") -> str:
    return f"{_CALENDAR_BASE}/calendars/{calendar_id}/events{suffix}"


def _rfc3339_utc(value: datetime) -> str:
    """Formata como RFC3339 UTC (sufixo "Z"), aceitando datetime aware ou
    naive. `.isoformat() + "Z"` sozinho quebra para datetimes aware — o
    isoformat() já inclui o offset ("+00:00"), então o "Z" extra produz
    "...+00:00Z", que a API do Google rejeita com 400 Bad Request."""
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value.isoformat() + "Z"


def authorization_url(state: str) -> str:
    """URL de consentimento. `access_type=offline&prompt=consent` garante que
    o Google devolva um refresh_token mesmo se o usuário já tiver autorizado
    este app antes — sem isso, reautorizações podem vir sem refresh_token."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_oauth_redirect_url,
        "response_type": "code",
        "scope": _SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            _TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_oauth_redirect_url,
                "grant_type": "authorization_code",
            },
        )
    _handle_error(response)
    return response.json()


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """O Google não reenvia um novo refresh_token aqui (reusa o mesmo) —
    quem chama deve manter o refresh_token original."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            _TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
    _handle_error(response)
    return response.json()


async def get_userinfo(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(_USERINFO_URL, headers=_headers(access_token))
    _handle_error(response)
    return response.json()


async def list_events(
    access_token: str,
    calendar_id: str,
    *,
    sync_token: str | None = None,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
) -> dict[str, Any]:
    """`singleEvents=true` expande instâncias de eventos recorrentes em itens
    individuais (ver requisito de não sincronizar recorrência). `sync_token`
    não pode ser combinado com `time_min`/`time_max` — a API do Google
    rejeita/ignora; a janela do sync incremental é fixada no full sync
    inicial. Levanta GoogleCalendarError(status_code=410) se o syncToken
    tiver expirado — quem chama deve refazer full sync."""
    params: dict[str, str] = {"singleEvents": "true"}
    if sync_token:
        params["syncToken"] = sync_token
    else:
        if time_min is not None:
            params["timeMin"] = _rfc3339_utc(time_min)
        if time_max is not None:
            params["timeMax"] = _rfc3339_utc(time_max)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(_events_url(calendar_id), headers=_headers(access_token), params=params)
    _handle_error(response)
    return response.json()


async def list_events_page(access_token: str, calendar_id: str, page_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            _events_url(calendar_id), headers=_headers(access_token), params={"pageToken": page_token}
        )
    _handle_error(response)
    return response.json()


async def insert_event(access_token: str, calendar_id: str, event_body: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(_events_url(calendar_id), headers=_headers(access_token), json=event_body)
    _handle_error(response)
    return response.json()


async def update_event(
    access_token: str, calendar_id: str, google_event_id: str, event_body: dict[str, Any]
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.patch(
            _events_url(calendar_id, f"/{google_event_id}"), headers=_headers(access_token), json=event_body
        )
    _handle_error(response)
    return response.json()


async def delete_event(access_token: str, calendar_id: str, google_event_id: str) -> None:
    """404/410 são tratados como sucesso (o evento já não existe no Google —
    idempotente, evita erro em exclusões repetidas ou fora de ordem)."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.delete(_events_url(calendar_id, f"/{google_event_id}"), headers=_headers(access_token))
    if response.status_code in (404, 410):
        return
    _handle_error(response)
