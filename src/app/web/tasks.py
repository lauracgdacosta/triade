"""Página de Tarefas: lista, formulário (modal HTMX) e ações rápidas."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.csrf import get_or_create_csrf_token, verify_csrf
from app.auth.dependencies import get_current_user_web
from app.database import get_db
from app.models.enums import Priority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.category_service import CategoryService
from app.services.goal_service import GoalService
from app.services.project_service import ProjectService
from app.services.role_service import RoleService
from app.services.tag_service import TagService
from app.services.task_service import TaskService
from app.templating import render
from app.web.context import base_context

router = APIRouter(prefix="/tasks", tags=["web-tasks"])


async def _form_options(db: AsyncSession, user_id: uuid.UUID) -> dict:
    return {
        "categories": await CategoryService(db).list(user_id),
        "projects": await ProjectService(db).list(user_id),
        "roles": await RoleService(db).list(user_id),
        "goals": await GoalService(db).list(user_id),
        "tags": await TagService(db).list(user_id),
    }


@router.get("", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    status_filter: str = "pending",
    q: str | None = None,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    context = await base_context(request, user, db)
    service = TaskService(db)
    tasks = await service.search(user.id, q) if q else await service.list_by_status(user.id, TaskStatus(status_filter))
    context.update({"tasks": tasks, "status_filter": status_filter, "q": q or "", "priorities": list(Priority)})
    return render(request, "pages/tasks.html", context)


@router.get("/list", response_class=HTMLResponse)
async def tasks_list_fragment(
    request: Request,
    status_filter: str = "pending",
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    tasks = await TaskService(db).list_by_status(user.id, TaskStatus(status_filter))
    return render(
        request, "fragments/task_list.html", {"request": request, "tasks": tasks, "status_filter": status_filter}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_task_form(
    request: Request,
    kanban_column_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    options = await _form_options(db, user.id)
    context = {
        "request": request, "task": None, **options,
        "priorities": list(Priority), "csrf_token": get_or_create_csrf_token(request),
        "prefill_kanban_column_id": str(kanban_column_id) if kanban_column_id else "",
    }
    return render(request, "fragments/task_form.html", context)


@router.get("/{task_id}/edit", response_class=HTMLResponse)
async def edit_task_form(
    task_id: uuid.UUID, request: Request, user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    task = await TaskService(db).get(task_id, user.id)
    options = await _form_options(db, user.id)
    context = {
        "request": request, "task": task, **options,
        "priorities": list(Priority), "csrf_token": get_or_create_csrf_token(request),
        "prefill_kanban_column_id": "",
    }
    return render(request, "fragments/task_form.html", context)


@router.post("", response_class=HTMLResponse)
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    notes: str = Form(""),
    date_: str = Form(""),
    time_: str = Form(""),
    planned_duration_minutes: str = Form(""),
    priority: str = Form("none"),
    category_id: str = Form(""),
    project_id: str = Form(""),
    goal_id: str = Form(""),
    role_id: str = Form(""),
    color: str = Form(""),
    location: str = Form(""),
    is_recurring: str = Form(""),
    kanban_column_id: str = Form(""),
    tag_ids: list[str] = Form([]),
    status_filter: str = Form("pending"),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    payload = TaskCreate(
        title=title,
        description=description or None,
        notes=notes or None,
        date=date.fromisoformat(date_) if date_ else None,
        time=time_ or None,
        planned_duration_minutes=int(planned_duration_minutes) if planned_duration_minutes else None,
        priority=Priority(priority),
        category_id=category_id or None,
        project_id=project_id or None,
        goal_id=goal_id or None,
        role_id=role_id or None,
        color=color or None,
        location=location or None,
        is_recurring=bool(is_recurring),
        kanban_column_id=kanban_column_id or None,
        tag_ids=[uuid.UUID(t) for t in tag_ids if t],
    )
    await TaskService(db).create(user.id, payload)
    tasks = await TaskService(db).list_by_status(user.id, TaskStatus(status_filter))
    return render(
        request,
        "fragments/task_list.html",
        {"request": request, "tasks": tasks, "status_filter": status_filter, "close_form": True},
    )


@router.post("/{task_id}", response_class=HTMLResponse)
async def update_task(
    task_id: uuid.UUID,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    notes: str = Form(""),
    date_: str = Form(""),
    time_: str = Form(""),
    planned_duration_minutes: str = Form(""),
    priority: str = Form("none"),
    category_id: str = Form(""),
    project_id: str = Form(""),
    goal_id: str = Form(""),
    role_id: str = Form(""),
    color: str = Form(""),
    location: str = Form(""),
    is_recurring: str = Form(""),
    tag_ids: list[str] = Form([]),
    status_filter: str = Form("pending"),
    csrf_token: str = Form(...),
    user: User = Depends(get_current_user_web),
    db: AsyncSession = Depends(get_db),
):
    await verify_csrf(request)
    service = TaskService(db)
    task = await service.get(task_id, user.id)
    payload = TaskUpdate(
        title=title,
        description=description or None,
        notes=notes or None,
        date=date.fromisoformat(date_) if date_ else None,
        time=time_ or None,
        planned_duration_minutes=int(planned_duration_minutes) if planned_duration_minutes else None,
        priority=Priority(priority),
        category_id=category_id or None,
        project_id=project_id or None,
        goal_id=goal_id or None,
        role_id=role_id or None,
        color=color or None,
        location=location or None,
        is_recurring=bool(is_recurring),
        tag_ids=[uuid.UUID(t) for t in tag_ids if t],
    )
    await service.update(task, payload)
    tasks = await service.list_by_status(user.id, TaskStatus(status_filter))
    return render(
        request,
        "fragments/task_list.html",
        {"request": request, "tasks": tasks, "status_filter": status_filter, "close_form": True},
    )


async def _action_and_refresh(request, service: TaskService, user: User, task_id: uuid.UUID, action: str, status_filter: str):
    task = await service.get(task_id, user.id)
    if task is not None:
        await getattr(service, action)(task)
    tasks = await service.list_by_status(user.id, TaskStatus(status_filter))
    return render(
        request, "fragments/task_list.html", {"request": request, "tasks": tasks, "status_filter": status_filter}
    )


@router.post("/{task_id}/complete", response_class=HTMLResponse)
async def complete_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "complete", status_filter)


@router.post("/{task_id}/cancel", response_class=HTMLResponse)
async def cancel_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "cancel", status_filter)


@router.post("/{task_id}/start", response_class=HTMLResponse)
async def start_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "start", status_filter)


@router.post("/{task_id}/wait", response_class=HTMLResponse)
async def wait_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "wait", status_filter)


@router.post("/{task_id}/reopen", response_class=HTMLResponse)
async def reopen_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "reopen", status_filter)


@router.post("/{task_id}/archive", response_class=HTMLResponse)
async def archive_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "archive", status_filter)


@router.post("/{task_id}/stop-recurrence", response_class=HTMLResponse)
async def stop_recurrence_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    return await _action_and_refresh(request, TaskService(db), user, task_id, "stop_recurrence", status_filter)


@router.post("/{task_id}/duplicate", response_class=HTMLResponse)
async def duplicate_task(
    task_id: uuid.UUID, request: Request, status_filter: str = Form("pending"),
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    service = TaskService(db)
    task = await service.get(task_id, user.id)
    if task is not None:
        await service.duplicate(task)
    tasks = await service.list_by_status(user.id, TaskStatus(status_filter))
    return render(
        request, "fragments/task_list.html", {"request": request, "tasks": tasks, "status_filter": status_filter}
    )


@router.delete("/{task_id}", response_class=HTMLResponse)
async def delete_task(
    task_id: uuid.UUID, request: Request, status_filter: str = "pending",
    user: User = Depends(get_current_user_web), db: AsyncSession = Depends(get_db)
):
    await verify_csrf(request)
    service = TaskService(db)
    task = await service.get(task_id, user.id)
    if task is not None:
        await service.delete(task)
    tasks = await service.list_by_status(user.id, TaskStatus(status_filter))
    return render(
        request, "fragments/task_list.html", {"request": request, "tasks": tasks, "status_filter": status_filter}
    )
