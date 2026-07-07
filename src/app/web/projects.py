"""Página de Projetos — CRUD via HTMX."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/projects", tags=["web-projects"])


async def _list_response(request: Request, service: ProjectService, user_id: uuid.UUID):
    projects = await service.list(user_id)
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request, "fragments/project_list.html", {"request": request, "projects": projects, "csrf_token": csrf_token}
    )


@router.get("", response_class=HTMLResponse)
async def projects_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    context["projects"] = await ProjectService(db).list(user.id)
    return render(request, "pages/projects.html", context)


@router.post("", response_class=HTMLResponse)
async def create_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("#22c55e"),
    deadline: str = Form(""),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = ProjectService(db)
    await service.create(
        user.id,
        ProjectCreate(
            name=name, description=description or None, color=color,
            deadline=date.fromisoformat(deadline) if deadline else None,
        ),
    )
    return await _list_response(request, service, user.id)


@router.post("/{project_id}", response_class=HTMLResponse)
async def update_project(
    project_id: uuid.UUID,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form(...),
    deadline: str = Form(""),
    percent_complete: float = Form(0),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = ProjectService(db)
    project = await service.get(project_id, user.id)
    if project is not None:
        await service.update(
            project,
            ProjectUpdate(
                name=name, description=description or None, color=color,
                deadline=date.fromisoformat(deadline) if deadline else None,
                percent_complete=percent_complete,
            ),
        )
    return await _list_response(request, service, user.id)


@router.delete("/{project_id}", response_class=HTMLResponse)
async def delete_project(
    project_id: uuid.UUID, request: Request,
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    service = ProjectService(db)
    project = await service.get(project_id, user.id)
    if project is not None:
        await service.delete(project)
    return await _list_response(request, service, user.id)
