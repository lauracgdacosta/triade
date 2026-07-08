"""Testes de integração das páginas web (server-rendered com Jinja2/HTMX)."""

import re

import pytest

pytestmark = pytest.mark.asyncio

PROTECTED_PAGES = [
    "/dashboard", "/tasks", "/agenda", "/kanban", "/categories",
    "/projects", "/roles", "/goals", "/pomodoro", "/settings", "/search", "/reports",
]


@pytest.mark.parametrize("path", PROTECTED_PAGES)
async def test_protected_page_redirects_when_not_authenticated(client, path):
    response = await client.get(path, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


@pytest.mark.parametrize("path", PROTECTED_PAGES)
async def test_protected_page_renders_when_authenticated(auth_client, path):
    response = await auth_client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


async def test_login_page_public(client):
    response = await client.get("/login")
    assert response.status_code == 200


async def test_index_redirects_to_login_when_anonymous(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


async def test_index_redirects_to_dashboard_when_authenticated(auth_client):
    response = await auth_client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


async def test_404_page(client):
    response = await client.get("/this-page-does-not-exist")
    assert response.status_code == 404


async def test_tasks_page_status_tabs_are_in_portuguese(auth_client):
    response = await auth_client.get("/tasks")
    assert "Pendente" in response.text
    assert "Em andamento" in response.text
    assert "Aguardando" in response.text
    assert "Concluída" in response.text
    assert "Cancelada" in response.text
    assert "Arquivada" in response.text
    assert "In Progress" not in response.text


async def test_create_task_via_htmx_form(auth_client):
    response = await auth_client.post(
        "/tasks",
        data={
            "title": "Via formulário HTMX",
            "priority": "none",
            "status_filter": "pending",
            "csrf_token": "irrelevant-because-header-based",
        },
        headers={"X-CSRF-Token": _get_csrf(await auth_client.get("/tasks"))},
    )
    assert response.status_code == 200
    assert "Via formulário HTMX" in response.text


async def test_create_recurring_task_and_stop_recurrence(auth_client):
    csrf = _get_csrf(await auth_client.get("/tasks"))
    response = await auth_client.post(
        "/tasks",
        data={
            "title": "Checar email",
            "time_": "08:00",
            "priority": "none",
            "status_filter": "pending",
            "is_recurring": "on",
            "csrf_token": "irrelevant-because-header-based",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    assert "Parar repetição" in response.text
    assert "fa-repeat" in response.text

    task_id = re.search(r"/tasks/([0-9a-f-]+)/stop-recurrence", response.text).group(1)

    stop_response = await auth_client.post(
        f"/tasks/{task_id}/stop-recurrence",
        data={"status_filter": "pending", "csrf_token": "irrelevant-because-header-based"},
        headers={"X-CSRF-Token": csrf},
    )
    assert stop_response.status_code == 200
    assert "Parar repetição" not in stop_response.text


def _get_csrf(response) -> str:
    marker = 'name="csrf-token" content="'
    start = response.text.index(marker) + len(marker)
    end = response.text.index('"', start)
    return response.text[start:end]
