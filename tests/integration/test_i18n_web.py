"""Testes de integração: a preferência de idioma do usuário afeta o texto renderizado."""

import pytest

pytestmark = pytest.mark.asyncio


def _get_csrf(response) -> str:
    marker = 'name="csrf-token" content="'
    start = response.text.index(marker) + len(marker)
    end = response.text.index('"', start)
    return response.text[start:end]


async def test_dashboard_renders_in_default_locale(auth_client):
    response = await auth_client.get("/dashboard")
    assert "Tarefas" in response.text
    assert "Configurações" in response.text


async def test_switching_language_changes_rendered_navigation(auth_client):
    csrf = _get_csrf(await auth_client.get("/settings"))
    update_res = await auth_client.post(
        "/settings",
        data={
            "theme": "auto", "language": "en-US", "time_format_24h": "true",
            "week_start_monday": "true", "default_task_duration_minutes": "30",
            "pomodoro_work_minutes": "25", "pomodoro_break_minutes": "5",
            "csrf_token": csrf,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert update_res.status_code == 200

    response = await auth_client.get("/dashboard")
    assert "Tasks" in response.text
    assert "Settings" in response.text
    assert "Tarefas" not in response.text
