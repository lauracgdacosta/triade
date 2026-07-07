"""Página de Busca global: resultados multi-entidade com filtros."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.enums import Priority, TaskStatus
from app.models.user import User
from app.schemas.search import SearchResponse
from app.services.category_service import CategoryService
from app.services.project_service import ProjectService
from app.services.role_service import RoleService
from app.services.search_service import SearchService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/search", tags=["web-search"])


@router.get("", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: str = "",
    category_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    role_id: uuid.UUID | None = None,
    priority: Priority | None = None,
    status_filter: TaskStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    context = await base_context(request, user, db)
    response = (
        await SearchService(db).search(
            user.id,
            q,
            category_id=category_id,
            project_id=project_id,
            role_id=role_id,
            priority=priority,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
        )
        if q
        else SearchResponse(query="")
    )
    context.update({
        "q": q,
        "response": response,
        "categories": await CategoryService(db).list(user.id),
        "projects": await ProjectService(db).list(user.id),
        "roles": await RoleService(db).list(user.id),
        "priorities": list(Priority),
        "statuses": list(TaskStatus),
        "category_id": category_id,
        "project_id": project_id,
        "role_id": role_id,
        "priority": priority,
        "status_filter": status_filter,
        "date_from": date_from,
        "date_to": date_to,
    })
    return render(request, "pages/search.html", context)
