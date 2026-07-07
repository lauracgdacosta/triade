"""Testes de integração da API REST do Kanban."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_get_default_board(auth_client):
    response = await auth_client.get("/api/v1/kanban/board")
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True
    assert len(data["columns"]) == 5


async def test_create_and_delete_column(auth_client):
    create_res = await auth_client.post("/api/v1/kanban/columns", json={"name": "Bloqueado", "color": "#ff0000"})
    assert create_res.status_code == 201
    column_id = create_res.json()["id"]

    board_res = await auth_client.get("/api/v1/kanban/board")
    assert len(board_res.json()["columns"]) == 6

    delete_res = await auth_client.delete(f"/api/v1/kanban/columns/{column_id}")
    assert delete_res.status_code == 204


async def test_move_task_to_column(auth_client):
    task_res = await auth_client.post("/api/v1/tasks", json={"title": "Mover no board"})
    task_id = task_res.json()["id"]

    board_res = await auth_client.get("/api/v1/kanban/board")
    target_column = board_res.json()["columns"][2]["id"]

    move_res = await auth_client.post(
        f"/api/v1/tasks/{task_id}/kanban-move", json={"kanban_column_id": target_column, "position": 0}
    )
    assert move_res.status_code == 200
    assert move_res.json()["kanban_column_id"] == target_column
