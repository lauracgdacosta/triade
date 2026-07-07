"""Página de Metas — CRUD via HTMX, com progresso calculado a partir das tarefas."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.goal_service import GoalService
from app.services.project_service import ProjectService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/goals", tags=["web-goals"])


async def _list_response(request: Request, goal_service: GoalService, project_service: ProjectService, user_id: uuid.UUID):
    goals = await goal_service.list(user_id)
    projects = await project_service.list(user_id)
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request,
        "fragments/goal_list.html",
        {"request": request, "goals": goals, "projects": projects, "csrf_token": csrf_token},
    )


@router.get("", response_class=HTMLResponse)
async def goals_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    context["goals"] = await GoalService(db).list(user.id)
    context["projects"] = await ProjectService(db).list(user.id)
    return render(request, "pages/goals.html", context)


@router.post("", response_class=HTMLResponse)
async def create_goal(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    project_id: str = Form(""),
    deadline: str = Form(""),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    goal_service, project_service = GoalService(db), ProjectService(db)
    await goal_service.create(
        user.id,
        GoalCreate(
            title=title, description=description or None, project_id=project_id or None,
            deadline=date.fromisoformat(deadline) if deadline else None,
        ),
    )
    return await _list_response(request, goal_service, project_service, user.id)


@router.post("/{goal_id}", response_class=HTMLResponse)
async def update_goal(
    goal_id: uuid.UUID,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    project_id: str = Form(""),
    deadline: str = Form(""),
    percent_complete: float = Form(0),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    goal_service, project_service = GoalService(db), ProjectService(db)
    goal = await goal_service.get(goal_id, user.id)
    if goal is not None:
        await goal_service.update(
            goal,
            GoalUpdate(
                title=title, description=description or None, project_id=project_id or None,
                deadline=date.fromisoformat(deadline) if deadline else None,
                percent_complete=percent_complete,
            ),
        )
    return await _list_response(request, goal_service, project_service, user.id)


@router.delete("/{goal_id}", response_class=HTMLResponse)
async def delete_goal(
    goal_id: uuid.UUID, request: Request,
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    goal_service, project_service = GoalService(db), ProjectService(db)
    goal = await goal_service.get(goal_id, user.id)
    if goal is not None:
        await goal_service.delete(goal)
    return await _list_response(request, goal_service, project_service, user.id)
