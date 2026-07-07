"""Enumerações compartilhadas entre models e schemas."""

import enum


class Priority(str, enum.Enum):
    IMPORTANT = "important"
    URGENT = "urgent"
    CIRCUMSTANTIAL = "circumstantial"
    NONE = "none"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    DONE = "done"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PomodoroMode(str, enum.Enum):
    CLASSIC_25_5 = "25_5"
    LONG_50_10 = "50_10"
    CUSTOM = "custom"


class PomodoroStatus(str, enum.Enum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TimeEntrySource(str, enum.Enum):
    MANUAL = "manual"
    POMODORO = "pomodoro"
    TIMER = "timer"


class ThemeMode(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class NotificationType(str, enum.Enum):
    TASK_DUE = "task_due"
    EVENT_REMINDER = "event_reminder"
    GOAL_DEADLINE = "goal_deadline"
    FOCUS_TIME = "focus_time"
