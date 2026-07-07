"""Testes de integração da API REST de Eventos/Agenda."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_create_and_list_events(auth_client):
    create_res = await auth_client.post(
        "/api/v1/events",
        json={"title": "Reunião", "start_at": "2026-05-01T09:00:00", "end_at": "2026-05-01T10:00:00"},
    )
    assert create_res.status_code == 201
    assert create_res.json()["has_conflict"] is False

    list_res = await auth_client.get(
        "/api/v1/events", params={"start": "2026-05-01T00:00:00", "end": "2026-05-02T00:00:00"}
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


async def test_conflicting_events_flagged(auth_client):
    await auth_client.post(
        "/api/v1/events",
        json={"title": "Primeiro", "start_at": "2026-05-01T09:00:00", "end_at": "2026-05-01T10:00:00"},
    )
    conflict_res = await auth_client.post(
        "/api/v1/events",
        json={"title": "Segundo", "start_at": "2026-05-01T09:30:00", "end_at": "2026-05-01T10:30:00"},
    )
    assert conflict_res.json()["has_conflict"] is True


async def test_update_and_delete_event(auth_client):
    create_res = await auth_client.post(
        "/api/v1/events",
        json={"title": "Original", "start_at": "2026-06-01T09:00:00", "end_at": "2026-06-01T10:00:00"},
    )
    event_id = create_res.json()["id"]

    patch_res = await auth_client.patch(f"/api/v1/events/{event_id}", json={"title": "Renomeado"})
    assert patch_res.json()["title"] == "Renomeado"

    delete_res = await auth_client.delete(f"/api/v1/events/{event_id}")
    assert delete_res.status_code == 204


async def test_event_invalid_range_rejected(auth_client):
    response = await auth_client.post(
        "/api/v1/events",
        json={"title": "Inválido", "start_at": "2026-06-01T10:00:00", "end_at": "2026-06-01T09:00:00"},
    )
    assert response.status_code == 422
