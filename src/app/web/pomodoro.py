"""Página do Cronômetro Pomodoro — timer roda no cliente (Alpine.js) e chama a API JSON."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.enums import TaskStatus
from app.models.user import User
from app.services.pomodoro_service import PomodoroService
from app.services.task_service import TaskService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/pomodoro", tags=["web-pomodoro"])


@router.get("", response_class=HTMLResponse)
async def pomodoro_page(request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)):
    context = await base_context(request, user, db)
    context["active_session"] = await PomodoroService(db).get_active(user.id)
    context["pending_tasks"] = await TaskService(db).list_by_status(user.id, TaskStatus.PENDING)
    return render(request, "pages/pomodoro.html", context)
