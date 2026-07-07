"""Página inicial: Dashboard 'Meu Dia'."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_optional, get_current_user_web
from app.database import get_db
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.templating import render
from app.web.context import base_context

router = APIRouter(tags=["web-dashboard"])


@router.get("/", response_class=HTMLResponse)
async def index(user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    context = await base_context(request, user, db)
    summary = await DashboardService(db).my_day(user.id)
    context["summary"] = summary
    return render(request, "pages/dashboard.html", context)
