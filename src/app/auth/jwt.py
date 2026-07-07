"""Verificação do JWT emitido pelo Supabase Auth.

Suporta os dois esquemas de assinatura usados pelo Supabase:
- **HS256** (legado): segredo compartilhado (`SUPABASE_JWT_SECRET`).
- **ES256/RS256** (projetos novos, "JWT Signing Keys"): chaves assimétricas
  publicadas no endpoint JWKS do projeto (`/auth/v1/.well-known/jwks.json`).

O algoritmo é lido do header do próprio token (`alg`) e tratado de acordo —
não é possível assumir um único esquema para todos os projetos Supabase.
"""

import time
from typing import Any

import httpx
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

_JWKS_TTL_SECONDS = 600
_jwks_cache: dict[str, Any] = {"keys": [], "fetched_at": 0.0}


class InvalidTokenError(Exception):
    pass


async def _get_jwks(force_refresh: bool = False) -> list[dict]:
    now = time.monotonic()
    if force_refresh or not _jwks_cache["keys"] or (now - _jwks_cache["fetched_at"]) > _JWKS_TTL_SECONDS:
        url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
        response.raise_for_status()
        _jwks_cache["keys"] = response.json().get("keys", [])
        _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


async def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """Decodifica e valida assinatura/expiração de um access_token do Supabase Auth."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    alg = header.get("alg", "HS256")

    try:
        if alg == "HS256":
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": bool(settings.supabase_jwt_secret)},
            )

        kid = header.get("kid")
        keys = await _get_jwks()
        key = next((k for k in keys if k.get("kid") == kid), None)
        if key is None:
            # a chave pode ter rotacionado; força um refresh antes de desistir
            keys = await _get_jwks(force_refresh=True)
            key = next((k for k in keys if k.get("kid") == kid), None)
        if key is None:
            raise InvalidTokenError(f"Chave JWKS não encontrada para kid={kid}")

        return jwt.decode(token, key, algorithms=[alg], audience="authenticated")
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
