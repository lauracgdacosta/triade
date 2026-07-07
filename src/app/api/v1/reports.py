"""Endpoints JSON de Relatórios e Estatísticas avançadas, consumidos pelo Chart.js."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_api
from app.database import get_db
from app.models.user import User
from app.schemas.report import ChartDataset, ReportSummary, StatsSummary
from app.services.report_service import ReportService
from app.services.stats_service import StatsService

router = APIRouter(prefix="/reports", tags=["reports"])

_DEFAULT_RANGE_DAYS = 30


def _default_range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=_DEFAULT_RANGE_DAYS))
    return start, end


@router.get("/time-by-project", response_model=ChartDataset)
async def time_by_project(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    start, end = _default_range(date_from, date_to)
    # Naive (sem tzinfo): TimeEntry.start_at/end_at não são timezone-aware no
    # Postgres — ver app.utils.datetime_utils.utcnow().
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    return await ReportService(db).time_by_project(user.id, start_dt, end_dt)


@router.get("/time-by-category", response_model=ChartDataset)
async def time_by_category(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    start, end = _default_range(date_from, date_to)
    # Naive (sem tzinfo): TimeEntry.start_at/end_at não são timezone-aware no
    # Postgres — ver app.utils.datetime_utils.utcnow().
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    return await ReportService(db).time_by_category(user.id, start_dt, end_dt)


@router.get("/time-by-role", response_model=ChartDataset)
async def time_by_role(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    start, end = _default_range(date_from, date_to)
    # Naive (sem tzinfo): TimeEntry.start_at/end_at não são timezone-aware no
    # Postgres — ver app.utils.datetime_utils.utcnow().
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    return await ReportService(db).time_by_role(user.id, start_dt, end_dt)


@router.get("/time-by-week", response_model=ChartDataset)
async def time_by_week(
    weeks: int = 8, user: User = Depends(get_current_user_api), db: AsyncSession = Depends(get_db)
):
    return await ReportService(db).time_by_week(user.id, weeks)


@router.get("/efficiency", response_model=ReportSummary)
async def efficiency(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    start, end = _default_range(date_from, date_to)
    return await ReportService(db).efficiency(user.id, start, end)


@router.get("/stats", response_model=StatsSummary)
async def stats(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user_api),
    db: AsyncSession = Depends(get_db),
):
    start, end = _default_range(date_from, date_to)
    return await StatsService(db).summary(user.id, start, end)
