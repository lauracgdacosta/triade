"""Página de Relatórios: gráficos (Chart.js) alimentados pelos endpoints de API."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.user import User
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/reports", tags=["web-reports"])


@router.get("", response_class=HTMLResponse)
async def reports_page(
    request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    context = await base_context(request, user, db)
    return render(request, "pages/reports.html", context)
