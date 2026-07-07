"""Proteção CSRF via double-submit cookie, para formulários/HTMX server-rendered.

Importante: o cookie precisa ser anexado à *própria* resposta retornada pela
rota (via `attach_csrf_cookie`), nunca a um objeto `Response` injetado à parte
— FastAPI não mescla cookies de um `Response` "sidecar" quando a rota retorna
seu próprio objeto de resposta (como um `TemplateResponse`).
"""

import secrets

from fastapi import HTTPException, Request, Response, status

from app.config import get_settings

settings = get_settings()

_HEADER_NAME = "X-CSRF-Token"
_FORM_FIELD = "csrf_token"


def get_or_create_csrf_token(request: Request) -> str:
    """Reaproveita o token já presente no cookie da requisição, ou gera um novo."""
    return request.cookies.get(settings.csrf_cookie_name) or secrets.token_urlsafe(32)


def attach_csrf_cookie(response: Response, token: str) -> None:
    """Define o cookie do token na resposta que será efetivamente enviada ao navegador."""
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        httponly=False,  # precisa ser lido pelo JS para ir no header do HTMX
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


async def verify_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    sent_token = request.headers.get(_HEADER_NAME)
    if not sent_token:
        form = await request.form()
        sent_token = form.get(_FORM_FIELD)
    if not cookie_token or not sent_token or not secrets.compare_digest(cookie_token, str(sent_token)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token CSRF inválido ou ausente.")
