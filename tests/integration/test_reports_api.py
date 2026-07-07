"""Testes de integração da API JSON de Relatórios e Estatísticas."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_time_by_project_returns_chart_shape(auth_client):
    response = await auth_client.get("/api/v1/reports/time-by-project")
    assert response.status_code == 200
    body = response.json()
    assert "labels" in body
    assert "values" in body


async def test_time_by_week_returns_chart_shape(auth_client):
    response = await auth_client.get("/api/v1/reports/time-by-week")
    assert response.status_code == 200
    body = response.json()
    assert "labels" in body
    assert "values" in body


async def test_efficiency_returns_summary_shape(auth_client):
    response = await auth_client.get("/api/v1/reports/efficiency")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "tasks_completed", "planned_minutes", "actual_minutes", "efficiency_percent", "avg_minutes_per_task",
    }


async def test_stats_returns_summary_shape(auth_client):
    response = await auth_client.get("/api/v1/reports/stats")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "streak_days", "completion_rate_percent", "lost_minutes", "overdue_tasks",
    }


async def test_reports_require_auth(client):
    response = await client.get("/api/v1/reports/stats")
    assert response.status_code == 401
