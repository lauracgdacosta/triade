"""Rotas OAuth do Google Calendar: conectar, callback, desconectar contas.

O `state` do OAuth é um mecanismo separado do CSRF do Tríade: precisa
sobreviver ao redirect completo ida-e-volta pro domínio do Google, por isso
vive num cookie próprio e efêmero (não o cookie de CSRF double-submit, que só
é reenviado em requests same-origin).
"""

import secrets
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import verify_csrf
from app.auth.dependencies import get_current_user_web
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services import google_calendar_client as client
from app.services.google_calendar_account_service import GoogleCalendarAccountService

router = APIRouter(prefix="/integrations/google", tags=["web-google-calendar"])

_STATE_COOKIE = "triade_google_oauth_state"
settings = get_settings()


def _set_state_cookie(response: RedirectResponse, state: str) -> None:
    response.set_cookie(
        _STATE_COOKIE, state, max_age=600, httponly=True,
        secure=settings.session_cookie_secure, samesite="lax", path="/",
    )


@router.get("/connect")
async def connect(user: User = Depends(get_current_user_web)):
    state = secrets.token_urlsafe(32)
    redirect = RedirectResponse(client.authorization_url(state), status_code=status.HTTP_303_SEE_OTHER)
    _set_state_cookie(redirect, state)
    return redirect


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    if error:
        redirect = RedirectResponse(f"/settings?google_error={error}", status_code=status.HTTP_303_SEE_OTHER)
        redirect.delete_cookie(_STATE_COOKIE, path="/")
        return redirect

    cookie_state = request.cookies.get(_STATE_COOKIE)
    if not code or not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Estado OAuth inválido ou expirado.")

    try:
        tokens = await client.exchange_code(code)
    except client.GoogleCalendarError:
        redirect = RedirectResponse("/settings?google_error=exchange_failed", status_code=status.HTTP_303_SEE_OTHER)
        redirect.delete_cookie(_STATE_COOKIE, path="/")
        return redirect

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        # Acontece se o usuário já tinha autorizado este app antes sem
        # revogar — o Google só reenvia refresh_token com prompt=consent
        # numa autorização "fresca". Sem ele não há como renovar o access
        # token depois de expirar, então não vale persistir a conta.
        redirect = RedirectResponse("/settings?google_error=no_refresh_token", status_code=status.HTTP_303_SEE_OTHER)
        redirect.delete_cookie(_STATE_COOKIE, path="/")
        return redirect

    try:
        userinfo = await client.get_userinfo(tokens["access_token"])
    except client.GoogleCalendarError:
        redirect = RedirectResponse("/settings?google_error=userinfo_failed", status_code=status.HTTP_303_SEE_OTHER)
        redirect.delete_cookie(_STATE_COOKIE, path="/")
        return redirect

    granted_scope = tokens.get("scope", "")
    if client.CALENDAR_SCOPE not in granted_scope.split():
        # A tela de consentimento do Google permite desmarcar escopos
        # individualmente — o usuário pode aprovar login (openid+email) e
        # negar o Calendar. Sem essa checagem a conta seria salva como
        # "conectada" e todo pull/push falharia depois com 403 silencioso
        # nos logs, sem sinalizar pro usuário que precisa reconectar.
        redirect = RedirectResponse("/settings?google_error=calendar_scope_denied", status_code=status.HTTP_303_SEE_OTHER)
        redirect.delete_cookie(_STATE_COOKIE, path="/")
        return redirect

    await GoogleCalendarAccountService(db).create_from_oauth(
        user.id,
        google_sub=userinfo["sub"],
        email=userinfo.get("email", ""),
        access_token=tokens["access_token"],
        refresh_token=refresh_token,
        expires_in=tokens.get("expires_in", 3600),
        scope=tokens.get("scope", ""),
    )
    redirect = RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(_STATE_COOKIE, path="/")
    return redirect


@router.post("/{account_id}/disconnect")
async def disconnect(
    account_id: uuid.UUID,
    request: Request,
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = GoogleCalendarAccountService(db)
    account = await service.get(account_id, user.id)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta não encontrada.")
    await service.disconnect(account)
    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)
