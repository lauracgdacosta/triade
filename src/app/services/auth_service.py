"""Orquestra o fluxo de autenticação: Supabase Auth + sincronização do perfil local."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import supabase_client
from app.auth.jwt import decode_supabase_jwt
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def sign_up(self, email: str, password: str) -> dict:
        return await supabase_client.sign_up(email, password)

    async def sign_in(self, email: str, password: str) -> dict:
        return await supabase_client.sign_in_with_password(email, password)

    async def sign_out(self, access_token: str) -> None:
        await supabase_client.sign_out(access_token)

    async def forgot_password(self, email: str) -> None:
        await supabase_client.request_password_reset(email)

    async def refresh(self, refresh_token: str) -> dict:
        return await supabase_client.refresh_session(refresh_token)

    def oauth_url(self, provider: str) -> str:
        return supabase_client.oauth_authorize_url(provider)

    async def sync_local_user_from_token(self, access_token: str) -> User:
        claims = await decode_supabase_jwt(access_token)
        user_id = uuid.UUID(claims["sub"])
        email = claims.get("email", "")
        return await self.users.get_or_create(user_id=user_id, email=email)
