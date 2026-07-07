"""Testes de integração do fluxo de autenticação (Supabase Auth mockado)."""

from unittest.mock import AsyncMock

import pytest

from app.auth import supabase_client

pytestmark = pytest.mark.asyncio


async def test_signup_success(client, monkeypatch):
    monkeypatch.setattr(
        supabase_client, "sign_up", AsyncMock(return_value={"user": {"id": "abc"}, "access_token": None})
    )
    response = await client.post(
        "/api/v1/auth/signup", json={"email": "new@example.com", "password": "supersecret123"}
    )
    assert response.status_code == 201
    assert response.json()["confirmation_required"] is True


async def test_signup_propagates_supabase_error(client, monkeypatch):
    async def _raise(*_args, **_kwargs):
        raise supabase_client.SupabaseAuthError("E-mail já cadastrado", 400)

    monkeypatch.setattr(supabase_client, "sign_up", _raise)
    response = await client.post(
        "/api/v1/auth/signup", json={"email": "dup@example.com", "password": "supersecret123"}
    )
    assert response.status_code == 400


async def test_login_sets_session_cookies(client, monkeypatch):
    monkeypatch.setattr(
        supabase_client,
        "sign_in_with_password",
        AsyncMock(
            return_value={
                "access_token": _fake_jwt(),
                "refresh_token": "refresh-token-value",
                "expires_in": 3600,
            }
        ),
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "supersecret123"}
    )
    assert response.status_code == 200
    assert "triade_at" in response.cookies


async def test_login_invalid_credentials(client, monkeypatch):
    async def _raise(*_args, **_kwargs):
        raise supabase_client.SupabaseAuthError("Credenciais inválidas", 400)

    monkeypatch.setattr(supabase_client, "sign_in_with_password", _raise)
    response = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong"}
    )
    assert response.status_code == 400


async def test_api_requires_authentication(client):
    response = await client.get("/api/v1/tasks")
    assert response.status_code == 401


async def test_authenticated_request_succeeds(auth_client):
    response = await auth_client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert response.json() == []


def _fake_jwt() -> str:
    from jose import jwt

    return jwt.encode({"sub": "11111111-1111-1111-1111-111111111111", "email": "user@example.com"}, "", algorithm="HS256")
