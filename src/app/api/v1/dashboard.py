"""Endpoint JSON do Dashboard 'Meu Dia'."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import MyDaySummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/my-day", response_model=MyDaySummary)
async def my_day(
    day: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.my_day(user.id, day)
