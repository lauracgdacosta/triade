"""Gerenciamento de cookies httpOnly de sessão (access_token / refresh_token)."""

from fastapi import Request, Response

from app.config import get_settings

settings = get_settings()

ACCESS_COOKIE = "triade_at"
REFRESH_COOKIE = "triade_rt"

_COOKIE_KWARGS = {
    "httponly": True,
    "secure": settings.session_cookie_secure,
    "samesite": "lax",
    "path": "/",
}


def set_session_cookies(response: Response, access_token: str, refresh_token: str, expires_in: int = 3600) -> None:
    response.set_cookie(ACCESS_COOKIE, access_token, max_age=expires_in, **_COOKIE_KWARGS)
    response.set_cookie(REFRESH_COOKIE, refresh_token, max_age=60 * 60 * 24 * 30, **_COOKIE_KWARGS)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def get_access_token(request: Request) -> str | None:
    return request.cookies.get(ACCESS_COOKIE)


def get_refresh_token(request: Request) -> str | None:
    return request.cookies.get(REFRESH_COOKIE)
