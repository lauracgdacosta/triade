"""Regra de negócio de Tarefas: CRUD + duplicar/arquivar/concluir/cancelar/reabrir."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskStatus
from app.models.task import Task
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.kanban_repository import KanbanBoardRepository, KanbanColumnRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import storage_service
from app.services.tag_service import TagService
from app.utils.datetime_utils import utcnow
from app.utils.sanitize import sanitize_html


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TaskRepository(db)
        self.attachment_repo = AttachmentRepository(db)
        self.tag_service = TagService(db)
        self.kanban_board_repo = KanbanBoardRepository(db)
        self.kanban_column_repo = KanbanColumnRepository(db)

    async def _kanban_column_id_for_status(self, user_id: uuid.UUID, status: TaskStatus) -> uuid.UUID | None:
        """Coluna do quadro padrão do usuário mapeada para `status` (se houver).

        Mantém Tarefas e Kanban em sincronia: mudar o status por aqui move o
        cartão para a coluna correspondente; colunas customizadas sem
        mapeamento (`maps_to_status is None`) simplesmente não participam.
        """
        board = await self.kanban_board_repo.get_default_for_user(user_id)
        if not board:
            return None
        return next((c.id for c in board.columns if c.maps_to_status == status), None)

    async def _status_updates(self, task: Task, status: TaskStatus, **extra: object) -> dict:
        """Monta o dict de atualização para uma troca de status, incluindo o
        reposicionamento no Kanban quando existir coluna mapeada."""
        updates: dict = {"status": status, **extra}
        column_id = await self._kanban_column_id_for_status(task.user_id, status)
        if column_id is not None:
            existing = await self.repo.list_by_kanban_column(task.user_id, column_id)
            updates["kanban_column_id"] = column_id
            updates["kanban_position"] = len(existing)
        return updates

    async def list_by_date(self, user_id: uuid.UUID, day):
        return await self.repo.list_by_date(user_id, day)

    async def list_between(self, user_id: uuid.UUID, start, end):
        return await self.repo.list_between_dates(user_id, start, end)

    async def list_by_status(self, user_id: uuid.UUID, status: TaskStatus):
        return await self.repo.list_by_status(user_id, status)

    async def search(self, user_id: uuid.UUID, query: str):
        return await self.repo.search(user_id, query)

    async def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        return await self.repo.get_for_user(task_id, user_id)

    async def create(self, user_id: uuid.UUID, data: TaskCreate) -> Task:
        payload = data.model_dump(exclude={"tag_ids"})
        payload["description"] = sanitize_html(payload.get("description"))
        payload["kanban_column_id"] = await self._kanban_column_id_for_status(user_id, TaskStatus.PENDING)
        task = await self.repo.create(user_id=user_id, **payload)
        if data.tag_ids:
            task.tags = await self.tag_service.get_or_create_many(user_id, data.tag_ids)
            await self.db.flush()
        return task

    async def update(self, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude={"tag_ids"}, exclude_unset=True)
        if "description" in payload:
            payload["description"] = sanitize_html(payload["description"])
        task = await self.repo.update(task, **payload)
        if data.tag_ids is not None:
            task.tags = await self.tag_service.get_or_create_many(task.user_id, data.tag_ids)
            await self.db.flush()
        return task

    async def delete(self, task: Task) -> None:
        for attachment in list(task.attachments):
            await storage_service.delete_attachment(attachment.file_url)
        await self.repo.delete(task)

    async def duplicate(self, task: Task) -> Task:
        clone = await self.repo.create(
            user_id=task.user_id,
            title=f"{task.title} (cópia)",
            description=task.description,
            notes=task.notes,
            date=task.date,
            time=task.time,
            planned_duration_minutes=task.planned_duration_minutes,
            priority=task.priority,
            category_id=task.category_id,
            project_id=task.project_id,
            goal_id=task.goal_id,
            role_id=task.role_id,
            color=task.color,
            location=task.location,
            kanban_column_id=task.kanban_column_id,
            kanban_position=task.kanban_position,
        )
        clone.tags = list(task.tags)
        await self.db.flush()
        return clone

    async def archive(self, task: Task) -> Task:
        return await self.repo.update(task, **await self._status_updates(task, TaskStatus.ARCHIVED))

    async def complete(self, task: Task) -> Task:
        updates = await self._status_updates(task, TaskStatus.DONE, completed_at=utcnow())
        return await self.repo.update(task, **updates)

    async def cancel(self, task: Task) -> Task:
        return await self.repo.update(task, **await self._status_updates(task, TaskStatus.CANCELLED))

    async def wait(self, task: Task) -> Task:
        return await self.repo.update(task, **await self._status_updates(task, TaskStatus.WAITING))

    async def start(self, task: Task) -> Task:
        return await self.repo.update(task, **await self._status_updates(task, TaskStatus.IN_PROGRESS))

    async def reopen(self, task: Task) -> Task:
        updates = await self._status_updates(task, TaskStatus.PENDING, completed_at=None)
        return await self.repo.update(task, **updates)

    async def move_to_kanban(self, task: Task, column_id: uuid.UUID, position: int) -> Task:
        updates: dict = {"kanban_column_id": column_id, "kanban_position": position}
        column = await self.kanban_column_repo.get(column_id)
        if column is not None and column.maps_to_status is not None:
            updates["status"] = column.maps_to_status
            if column.maps_to_status == TaskStatus.DONE:
                updates["completed_at"] = utcnow()
            elif task.status == TaskStatus.DONE:
                updates["completed_at"] = None
        return await self.repo.update(task, **updates)

    async def add_attachment(
        self, task: Task, file_name: str, content: bytes, content_type: str
    ):
        file_url = await storage_service.upload_attachment(
            task.user_id, task.id, file_name, content, content_type
        )
        return await self.attachment_repo.create(
            task_id=task.id,
            file_name=file_name,
            file_url=file_url,
            mime_type=content_type,
            size_bytes=len(content),
        )

    async def remove_attachment(self, attachment) -> None:
        await storage_service.delete_attachment(attachment.file_url)
        await self.attachment_repo.delete(attachment)
