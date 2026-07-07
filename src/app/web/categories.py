"""Página de Categorias (CRUD via HTMX)."""

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/categories", tags=["web-categories"])


async def _list_response(request: Request, service: CategoryService, user_id: uuid.UUID):
    categories = await service.list(user_id)
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request, "fragments/category_list.html", {"request": request, "categories": categories, "csrf_token": csrf_token}
    )


@router.get("", response_class=HTMLResponse)
async def categories_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    context["categories"] = await CategoryService(db).list(user.id)
    return render(request, "pages/categories.html", context)


@router.post("", response_class=HTMLResponse)
async def create_category(
    request: Request,
    name: str = Form(...),
    icon: str = Form("fa-solid fa-tag"),
    color: str = Form("#0ea5e9"),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = CategoryService(db)
    await service.create(user.id, CategoryCreate(name=name, icon=icon, color=color))
    return await _list_response(request, service, user.id)


@router.post("/{category_id}", response_class=HTMLResponse)
async def update_category(
    category_id: uuid.UUID,
    request: Request,
    name: str = Form(...),
    icon: str = Form(...),
    color: str = Form(...),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = CategoryService(db)
    category = await service.get(category_id, user.id)
    if category is not None:
        await service.update(category, CategoryUpdate(name=name, icon=icon, color=color))
    return await _list_response(request, service, user.id)


@router.delete("/{category_id}", response_class=HTMLResponse)
async def delete_category(
    category_id: uuid.UUID, request: Request,
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    service = CategoryService(db)
    category = await service.get(category_id, user.id)
    if category is not None:
        await service.delete(category)
    return await _list_response(request, service, user.id)
