"""Testes do AuthService: sincronização do usuário local a partir do JWT."""

import uuid

import pytest
from jose import jwt as jose_jwt

from app.services.auth_service import AuthService

pytestmark = pytest.mark.asyncio


async def test_sync_local_user_from_token_creates_user(db_session):
    user_id = uuid.uuid4()
    token = jose_jwt.encode({"sub": str(user_id), "email": "sync@example.com"}, "", algorithm="HS256")

    service = AuthService(db_session)
    user = await service.sync_local_user_from_token(token)
    assert user.id == user_id
    assert user.email == "sync@example.com"


async def test_oauth_url_contains_provider():
    service = AuthService.__new__(AuthService)  # não precisa de sessão para este método
    url = service.oauth_url("google")
    assert "provider=google" in url
