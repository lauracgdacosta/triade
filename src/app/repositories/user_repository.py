"""Persistência do perfil local de usuário (espelho do Supabase Auth)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kanban import DEFAULT_KANBAN_COLUMNS, KanbanBoard, KanbanColumn
from app.models.settings import UserSettings
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID, email: str) -> User:
        user = await self.get(user_id)
        if user is not None:
            return user

        user = User(id=user_id, email=email)
        self.session.add(user)
        # flush isolado: garante que a linha em `users` exista antes de inserir
        # as tabelas dependentes (obrigatório com FKs aplicadas, como no Postgres).
        await self.session.flush()

        self.session.add(UserSettings(user_id=user_id))

        board = KanbanBoard(user_id=user_id, name="Meu Quadro", is_default=True)
        board.columns = [
            KanbanColumn(name=col["name"], color=col["color"], position=i)
            for i, col in enumerate(DEFAULT_KANBAN_COLUMNS)
        ]
        self.session.add(board)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_profile(self, user: User, **kwargs: object) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self.session.flush()
        await self.session.refresh(user)
        return user
