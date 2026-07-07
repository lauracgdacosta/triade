"""Cliente HTTP fino para a API REST do Supabase Auth (GoTrue) e Storage.

Mantém o fluxo de autenticação inteiramente no servidor: o front-end nunca fala
diretamente com o Supabase, apenas envia formulários HTML/HTMX para nossas rotas
`web.auth`, que por sua vez chamam este cliente.
"""

from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()


class SupabaseAuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _auth_url(path: str) -> str:
    return f"{settings.supabase_url}/auth/v1{path}"


def _headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }
    headers["Authorization"] = f"Bearer {access_token or settings.supabase_anon_key}"
    return headers


async def _post(path: str, json: dict[str, Any], access_token: str | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(_auth_url(path), json=json, headers=_headers(access_token))
    if response.status_code >= 400:
        detail = response.json().get("error_description") or response.json().get("msg") or response.text
        raise SupabaseAuthError(detail, response.status_code)
    return response.json()


async def sign_up(email: str, password: str) -> dict[str, Any]:
    """Cria o usuário no Supabase Auth. Dispara e-mail de confirmação (configurado no projeto)."""
    return await _post(
        "/signup",
        {"email": email, "password": password, "options": {"email_redirect_to": settings.oauth_redirect_url}},
    )


async def sign_in_with_password(email: str, password: str) -> dict[str, Any]:
    return await _post("/token?grant_type=password", {"email": email, "password": password})


async def refresh_session(refresh_token: str) -> dict[str, Any]:
    return await _post("/token?grant_type=refresh_token", {"refresh_token": refresh_token})


async def sign_out(access_token: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(_auth_url("/logout"), headers=_headers(access_token))


async def request_password_reset(email: str) -> None:
    await _post("/recover", {"email": email, "options": {"redirect_to": settings.oauth_redirect_url}})


def oauth_authorize_url(provider: str) -> str:
    """URL para redirecionar o navegador do usuário e iniciar o login OAuth (Google/GitHub)."""
    return (
        f"{settings.supabase_url}/auth/v1/authorize"
        f"?provider={provider}&redirect_to={settings.oauth_redirect_url}"
    )


async def get_user(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(_auth_url("/user"), headers=_headers(access_token))
    if response.status_code >= 400:
        raise SupabaseAuthError("Sessão inválida ou expirada.", response.status_code)
    return response.json()
