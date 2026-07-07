"""Página do Kanban — o quadro renderizado no servidor; drag-and-drop via JS/fetch."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_web
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.kanban_service import KanbanService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/kanban", tags=["web-kanban"])


@router.get("", response_class=HTMLResponse)
async def kanban_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    board, tasks_by_column = await KanbanService(db).board_with_tasks(user.id)
    context["board"] = board
    context["tasks_by_column"] = tasks_by_column
    settings = get_settings()
    context["supabase_url"] = settings.supabase_url
    context["supabase_anon_key"] = settings.supabase_anon_key
    return render(request, "pages/kanban.html", context)
