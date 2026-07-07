"""Agregador dos routers JSON (api/v1), documentados automaticamente no Swagger."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    categories,
    dashboard,
    events,
    goals,
    kanban,
    me,
    notes,
    notifications,
    pomodoro,
    projects,
    reports,
    roles,
    search,
    tags,
    tasks,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(dashboard.router)
api_router.include_router(tasks.router)
api_router.include_router(events.router)
api_router.include_router(kanban.router)
api_router.include_router(categories.router)
api_router.include_router(projects.router)
api_router.include_router(roles.router)
api_router.include_router(goals.router)
api_router.include_router(tags.router)
api_router.include_router(pomodoro.router)
api_router.include_router(notes.router)
api_router.include_router(notifications.router)
api_router.include_router(search.router)
api_router.include_router(reports.router)
