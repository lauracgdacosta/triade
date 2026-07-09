"""Testes de integração da API REST de Tarefas."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app

pytestmark = pytest.mark.asyncio


async def test_create_and_get_task(auth_client):
    create_res = await auth_client.post("/api/v1/tasks", json={"title": "Tarefa via API"})
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    get_res = await auth_client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Tarefa via API"


async def test_create_task_with_kanban_column_id_lands_in_that_column(auth_client):
    board = (await auth_client.get("/api/v1/kanban/board")).json()
    done_column = next(c for c in board["columns"] if c["maps_to_status"] == "done")

    create_res = await auth_client.post(
        "/api/v1/tasks", json={"title": "Direto no Concluído", "kanban_column_id": done_column["id"]}
    )
    assert create_res.status_code == 201
    body = create_res.json()
    assert body["kanban_column_id"] == done_column["id"]
    assert body["status"] == "done"


async def test_update_task(auth_client):
    create_res = await auth_client.post("/api/v1/tasks", json={"title": "Original"})
    task_id = create_res.json()["id"]

    patch_res = await auth_client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Atualizada"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Atualizada"


async def test_task_lifecycle_actions(auth_client):
    create_res = await auth_client.post("/api/v1/tasks", json={"title": "Ciclo de vida"})
    task_id = create_res.json()["id"]

    complete_res = await auth_client.post(f"/api/v1/tasks/{task_id}/complete")
    assert complete_res.json()["status"] == "done"

    reopen_res = await auth_client.post(f"/api/v1/tasks/{task_id}/reopen")
    assert reopen_res.json()["status"] == "pending"

    cancel_res = await auth_client.post(f"/api/v1/tasks/{task_id}/cancel")
    assert cancel_res.json()["status"] == "cancelled"


async def test_duplicate_and_archive(auth_client):
    create_res = await auth_client.post("/api/v1/tasks", json={"title": "Duplicar"})
    task_id = create_res.json()["id"]

    dup_res = await auth_client.post(f"/api/v1/tasks/{task_id}/duplicate")
    assert dup_res.status_code == 201
    assert dup_res.json()["title"] == "Duplicar (cópia)"

    archive_res = await auth_client.post(f"/api/v1/tasks/{task_id}/archive")
    assert archive_res.json()["status"] == "archived"


async def test_delete_task(auth_client):
    create_res = await auth_client.post("/api/v1/tasks", json={"title": "Excluir"})
    task_id = create_res.json()["id"]

    delete_res = await auth_client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_res.status_code == 204

    get_res = await auth_client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 404


async def test_task_not_found_returns_404(auth_client):
    response = await auth_client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_cannot_access_other_users_task(auth_client):
    create_res = await auth_client.post("/api/v1/tasks", json={"title": "Privada"})
    task_id = create_res.json()["id"]

    # cliente novo, sem cookie de sessão (não autenticado), não deve conseguir acessar
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon_client:
        response = await anon_client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 401
