"""Agregador das rotas web (páginas server-rendered com HTMX/Jinja2)."""

from fastapi import APIRouter

from app.web import (
    agenda,
    auth,
    categories,
    dashboard,
    goals,
    google_calendar,
    kanban,
    notes,
    notifications,
    pomodoro,
    projects,
    reports,
    roles,
    search,
    settings,
    tasks,
)

web_router = APIRouter()
web_router.include_router(auth.router)
web_router.include_router(dashboard.router)
web_router.include_router(tasks.router)
web_router.include_router(agenda.router)
web_router.include_router(google_calendar.router)
web_router.include_router(kanban.router)
web_router.include_router(categories.router)
web_router.include_router(projects.router)
web_router.include_router(roles.router)
web_router.include_router(goals.router)
web_router.include_router(pomodoro.router)
web_router.include_router(settings.router)
web_router.include_router(notes.router)
web_router.include_router(notifications.router)
web_router.include_router(search.router)
web_router.include_router(reports.router)
