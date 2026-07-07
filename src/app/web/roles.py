"""Página de Papéis (Roles) — CRUD via HTMX."""

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.role_service import RoleService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/roles", tags=["web-roles"])


async def _list_response(request: Request, service: RoleService, user_id: uuid.UUID):
    roles = await service.list(user_id)
    csrf_token = get_or_create_csrf_token(request)
    return render(request, "fragments/role_list.html", {"request": request, "roles": roles, "csrf_token": csrf_token})


@router.get("", response_class=HTMLResponse)
async def roles_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    context["roles"] = await RoleService(db).list(user.id)
    return render(request, "pages/roles.html", context)


@router.post("", response_class=HTMLResponse)
async def create_role(
    request: Request,
    name: str = Form(...),
    icon: str = Form("fa-solid fa-briefcase"),
    color: str = Form("#6366f1"),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = RoleService(db)
    await service.create(user.id, RoleCreate(name=name, icon=icon, color=color))
    return await _list_response(request, service, user.id)


@router.post("/{role_id}", response_class=HTMLResponse)
async def update_role(
    role_id: uuid.UUID,
    request: Request,
    name: str = Form(...),
    icon: str = Form(...),
    color: str = Form(...),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = RoleService(db)
    role = await service.get(role_id, user.id)
    if role is not None:
        await service.update(role, RoleUpdate(name=name, icon=icon, color=color))
    return await _list_response(request, service, user.id)


@router.delete("/{role_id}", response_class=HTMLResponse)
async def delete_role(
    role_id: uuid.UUID, request: Request,
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    service = RoleService(db)
    role = await service.get(role_id, user.id)
    if role is not None:
        await service.delete(role)
    return await _list_response(request, service, user.id)
