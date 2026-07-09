"""Testes de integração do fluxo OAuth do Google Calendar (conectar/callback/desconectar)."""

import re
import uuid

import httpx
import pytest
import respx

pytestmark = pytest.mark.asyncio


def _get_csrf(response) -> str:
    marker = 'name="csrf-token" content="'
    start = response.text.index(marker) + len(marker)
    return response.text[start : response.text.index('"', start)]


async def test_connect_sets_state_cookie_and_redirects_to_google(auth_client):
    response = await auth_client.get("/integrations/google/connect", follow_redirects=False)
    assert response.status_code == 303
    assert "accounts.google.com" in response.headers["location"]
    assert "triade_google_oauth_state" in response.cookies


async def test_callback_without_state_cookie_returns_400(auth_client):
    response = await auth_client.get("/integrations/google/callback?code=abc&state=whatever")
    assert response.status_code == 400


async def test_callback_with_mismatched_state_returns_400(auth_client):
    await auth_client.get("/integrations/google/connect", follow_redirects=False)
    response = await auth_client.get("/integrations/google/callback?code=abc&state=state-invalido")
    assert response.status_code == 400


async def test_callback_with_error_redirects_to_settings(auth_client):
    connect_res = await auth_client.get("/integrations/google/connect", follow_redirects=False)
    state = re.search(r"state=([^&]+)", connect_res.headers["location"]).group(1)

    response = await auth_client.get(
        f"/integrations/google/callback?error=access_denied&state={state}", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings?google_error=access_denied"


@respx.mock
async def test_callback_happy_path_creates_account(auth_client):
    connect_res = await auth_client.get("/integrations/google/connect", follow_redirects=False)
    state = re.search(r"state=([^&]+)", connect_res.headers["location"]).group(1)

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "at-1",
                "refresh_token": "rt-1",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/calendar",
            },
        )
    )
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(200, json={"sub": "sub-1", "email": "trabalho@example.com"})
    )

    response = await auth_client.get(
        f"/integrations/google/callback?code=abc123&state={state}", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings"

    settings_page = await auth_client.get("/settings")
    assert "trabalho@example.com" in settings_page.text


@respx.mock
async def test_callback_without_refresh_token_does_not_persist_account(auth_client):
    connect_res = await auth_client.get("/integrations/google/connect", follow_redirects=False)
    state = re.search(r"state=([^&]+)", connect_res.headers["location"]).group(1)

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "at-1", "expires_in": 3600})
    )

    response = await auth_client.get(
        f"/integrations/google/callback?code=abc123&state={state}", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings?google_error=no_refresh_token"


@respx.mock
async def test_callback_without_calendar_scope_does_not_persist_account(auth_client):
    """Usuário pode desmarcar o escopo do Calendar na tela de consentimento
    do Google e ainda assim aprovar login (openid+email) — sem essa
    checagem a conta seria salva como "conectada" e todo sync falharia
    depois com 403 silencioso."""
    connect_res = await auth_client.get("/integrations/google/connect", follow_redirects=False)
    state = re.search(r"state=([^&]+)", connect_res.headers["location"]).group(1)

    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "at-1",
                "refresh_token": "rt-1",
                "expires_in": 3600,
                "scope": "openid email",
            },
        )
    )
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(200, json={"sub": "sub-1", "email": "trabalho@example.com"})
    )

    response = await auth_client.get(
        f"/integrations/google/callback?code=abc123&state={state}", follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings?google_error=calendar_scope_denied"

    settings_page = await auth_client.get("/settings")
    assert "trabalho@example.com" not in settings_page.text


async def test_disconnect_without_csrf_is_rejected(auth_client):
    response = await auth_client.post(
        f"/integrations/google/{uuid.uuid4()}/disconnect", data={"csrf_token": "forjado"}
    )
    assert response.status_code == 403


async def test_disconnect_unknown_account_returns_404(auth_client):
    page = await auth_client.get("/settings")
    token = _get_csrf(page)
    response = await auth_client.post(
        f"/integrations/google/{uuid.uuid4()}/disconnect",
        data={"csrf_token": token},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 404
