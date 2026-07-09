"""Fixtures compartilhadas: banco SQLite em memória, cliente HTTP e usuário autenticado."""

import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  garante que Base.metadata conheça todas as tabelas
from app.config import get_settings
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models.kanban import DEFAULT_KANBAN_COLUMNS, KanbanBoard, KanbanColumn
from app.models.settings import UserSettings
from app.models.user import User

# Os testes assinam JWTs "falsos" com segredo vazio (ver `make_access_token`
# abaixo). Isso precisa valer independentemente de um `.env` real (com
# SUPABASE_JWT_SECRET de produção) existir na máquina — caso contrário a
# suíte de testes fica acoplada ao ambiente local de quem a executa.
get_settings().supabase_jwt_secret = ""

# Idem para a chave de criptografia dos tokens do Google Calendar (ver
# app/utils/crypto.py) — precisa existir independentemente de um `.env` real.
get_settings().google_token_encryption_key = Fernet.generate_key().decode()

test_engine = create_async_engine(
    "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)


@event.listens_for(test_engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def _override_get_db() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


fastapi_app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def _setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(id=uuid.uuid4(), email="test@example.com", display_name="Test User")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserSettings(user_id=user.id))

    board = KanbanBoard(user_id=user.id, name="Meu Quadro", is_default=True)
    board.columns = [
        KanbanColumn(name=c["name"], color=c["color"], position=i, maps_to_status=c["status"])
        for i, c in enumerate(DEFAULT_KANBAN_COLUMNS)
    ]
    db_session.add(board)

    await db_session.commit()
    await db_session.refresh(user)
    return user


def make_access_token(user: User) -> str:
    return jwt.encode({"sub": str(user.id), "email": user.email}, "", algorithm="HS256")


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, test_user: User) -> AsyncClient:
    client.cookies.set("triade_at", make_access_token(test_user))
    return client
