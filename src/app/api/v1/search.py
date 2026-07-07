"""Endpoint JSON de Busca global."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.enums import Priority, TaskStatus
from app.models.user import User
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str,
    category_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    role_id: uuid.UUID | None = None,
    priority: Priority | None = None,
    status_filter: TaskStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    return await SearchService(db).search(
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
