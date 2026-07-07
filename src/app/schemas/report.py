"""Schemas de Relatórios e Estatísticas avançadas."""

from pydantic import Field

from app.schemas.common import ORMModel


class ChartDataset(ORMModel):
    labels: list[str] = Field(default_factory=list)
    values: list[int] = Field(default_factory=list)


class ReportSummary(ORMModel):
    tasks_completed: int
    planned_minutes: int
    actual_minutes: int
    efficiency_percent: float
    avg_minutes_per_task: float


class StatsSummary(ORMModel):
    streak_days: int
    completion_rate_percent: float
    lost_minutes: int
    overdue_tasks: int
