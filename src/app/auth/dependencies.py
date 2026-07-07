"""Dependências de autenticação para rotas de API (JSON) e Web (HTMX/páginas)."""

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import InvalidTokenError, decode_supabase_jwt
from app.auth.session import get_access_token
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthRedirectError(Exception):
    """Sinaliza que uma rota `web` precisa redirecionar o navegador para /login."""


@dataclass
class CurrentUser:
    id: uuid.UUID
    email: str


async def _decode_or_none(access_token: str | None) -> CurrentUser | None:
    if not access_token:
        return None
    try:
        claims = await decode_supabase_jwt(access_token)
    except InvalidTokenError:
        return None
    return CurrentUser(id=uuid.UUID(claims["sub"]), email=claims.get("email", ""))


async def get_current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User | None:
    claims_user = await _decode_or_none(get_access_token(request))
    if claims_user is None:
        return None
    repo = UserRepository(db)
    return await repo.get_or_create(user_id=claims_user.id, email=claims_user.email)


async def get_current_user_api(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Não autenticado.")
    return user


async def get_current_user_web(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise AuthRedirectError
    return user
