"""Schema agregado do Dashboard 'Meu Dia'."""

from datetime import date

from pydantic import BaseModel

from app.schemas.task import TaskRead


class MyDaySummary(BaseModel):
    today: date
    greeting: str
    tasks_total: int
    tasks_done: int
    progress_percent: float
    planned_minutes: int
    actual_minutes: int
    remaining_minutes: int
    tasks: list[TaskRead]
