"""Importa todos os models para popular `Base.metadata` (usado por Alembic e testes)."""

from app.models.attachment import Attachment
from app.models.category import Category
from app.models.event import Event
from app.models.goal import Goal
from app.models.google_calendar_account import GoogleCalendarAccount
from app.models.kanban import KanbanBoard, KanbanColumn
from app.models.note import Note
from app.models.notification import Notification
from app.models.pomodoro import PomodoroSession
from app.models.project import Project
from app.models.role import Role
from app.models.settings import UserSettings
from app.models.tag import Tag, task_tags
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.models.user import User

__all__ = [
    "Attachment",
    "Category",
    "Event",
    "Goal",
    "GoogleCalendarAccount",
    "KanbanBoard",
    "KanbanColumn",
    "Note",
    "Notification",
    "PomodoroSession",
    "Project",
    "Role",
    "UserSettings",
    "Tag",
    "task_tags",
    "Task",
    "TimeEntry",
    "User",
]
