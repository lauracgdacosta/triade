"""Testes do formulário de tarefa inline (sem modal): fecha só após salvar."""

import re

import pytest

pytestmark = pytest.mark.asyncio


def _get_csrf(response) -> str:
    marker = 'name="csrf-token" content="'
    start = response.text.index(marker) + len(marker)
    end = response.text.index('"', start)
    return response.text[start:end]


async def test_full_page_load_has_single_form_container(auth_client):
    """Evita regressão: o container não pode aparecer duplicado (um explícito
    em pages/tasks.html + um vindo do fragment incluído), o que quebraria
    document.getElementById e geraria HTML inválido (IDs duplicados)."""
    response = await auth_client.get("/tasks")
    assert response.text.count('id="task-form-container"') == 1


async def test_create_task_response_closes_form_via_oob_swap(auth_client):
    csrf = _get_csrf(await auth_client.get("/tasks"))
    headers = {"X-CSRF-Token": csrf}
    response = await auth_client.post(
        "/tasks",
        data={"title": "Fecha ao salvar", "priority": "none", "status_filter": "pending", "csrf_token": "x"},
        headers=headers,
    )
    assert response.status_code == 200
    assert 'id="task-form-container" hx-swap-oob="true"' in response.text
    assert "Fecha ao salvar" in response.text


async def test_update_task_response_closes_form_via_oob_swap(auth_client):
    csrf = _get_csrf(await auth_client.get("/tasks"))
    headers = {"X-CSRF-Token": csrf}
    create_res = await auth_client.post(
        "/tasks",
        data={"title": "Original", "priority": "none", "status_filter": "pending", "csrf_token": "x"},
        headers=headers,
    )
    task_id = re.search(r'hx-post="/tasks/([0-9a-f-]{36})/complete"', create_res.text).group(1)

    update_res = await auth_client.post(
        f"/tasks/{task_id}",
        data={"title": "Atualizada", "priority": "none", "status_filter": "pending", "csrf_token": "x"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert 'id="task-form-container" hx-swap-oob="true"' in update_res.text


async def test_other_task_actions_do_not_close_form(auth_client):
    """Ações disparadas pela lista (concluir, duplicar, etc.) não têm o
    formulário aberto — não devem mandar o swap OOB (comportamento correto,
    embora inofensivo se mandassem)."""
    csrf = _get_csrf(await auth_client.get("/tasks"))
    headers = {"X-CSRF-Token": csrf}
    create_res = await auth_client.post(
        "/tasks",
        data={"title": "Para concluir", "priority": "none", "status_filter": "pending", "csrf_token": "x"},
        headers=headers,
    )
    task_id = re.search(r'hx-post="/tasks/([0-9a-f-]{36})/complete"', create_res.text).group(1)

    complete_res = await auth_client.post(
        f"/tasks/{task_id}/complete", data={"status_filter": "pending"}, headers=headers
    )
    assert "hx-swap-oob" not in complete_res.text
