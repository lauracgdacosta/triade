"""Busca global multi-entidade (tarefas, projetos, metas, eventos) com filtros."""

import asyncio
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Priority, TaskStatus
from app.repositories.event_repository import EventRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.search import SearchResponse, SearchResult


class SearchService:
    def __init__(self, db: AsyncSession):
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.goal_repo = GoalRepository(db)
        self.event_repo = EventRepository(db)

    async def search(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        category_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        role_id: uuid.UUID | None = None,
        priority: Priority | None = None,
        status: TaskStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> SearchResponse:
        tasks, projects, goals, events = await asyncio.gather(
            self.task_repo.search(user_id, query),
            self.project_repo.search(user_id, query),
            self.goal_repo.search(user_id, query),
            self.event_repo.search(user_id, query),
        )

        def task_matches(task) -> bool:
            if category_id and task.category_id != category_id:
                return False
            if project_id and task.project_id != project_id:
                return False
            if role_id and task.role_id != role_id:
                return False
            if priority and task.priority != priority:
                return False
            if status and task.status != status:
                return False
            if date_from and (task.date is None or task.date < date_from):
                return False
            return not (date_to and (task.date is None or task.date > date_to))

        results = [
            SearchResult(
                entity_type="task",
                id=task.id,
                title=task.title,
                subtitle=task.date.strftime("%d/%m/%Y") if task.date else None,
                url=f"/tasks?status_filter={task.status.value}",
            )
            for task in tasks
            if task_matches(task)
        ]
        results += [
            SearchResult(entity_type="project", id=project.id, title=project.name, url="/projects")
            for project in projects
        ]
        results += [
            SearchResult(
                entity_type="goal",
                id=goal.id,
                title=goal.title,
                subtitle=goal.deadline.strftime("%d/%m/%Y") if goal.deadline else None,
                url="/goals",
            )
            for goal in goals
        ]
        results += [
            SearchResult(
                entity_type="event",
                id=event.id,
                title=event.title,
                subtitle=event.start_at.strftime("%d/%m/%Y %H:%M"),
                url="/agenda",
            )
            for event in events
        ]

        return SearchResponse(query=query, results=results, total=len(results))
