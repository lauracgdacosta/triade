"""Engine/sessão async do SQLAlchemy 2.0."""

from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

_engine_kwargs = {"echo": settings.app_debug and not settings.is_production}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
elif settings.database_url.startswith("postgresql"):
    # O pooler do Supabase (pgbouncer, pool_mode=transaction) não suporta prepared
    # statements nomeados sequencialmente: conexões diferentes podem reutilizar o
    # mesmo nome ("__asyncpg_stmt_1__") e colidir. Nomes únicos via uuid4 evitam o
    # DuplicatePreparedStatementError; NullPool evita acumular prepared statements
    # órfãos em conexões que o pgbouncer já reciclou.
    _engine_kwargs["poolclass"] = NullPool
    _engine_kwargs["connect_args"] = {
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    }

engine = create_async_engine(settings.database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os models."""


async def get_db() -> AsyncIterator[AsyncSession]:
    """Unit of work por requisição: commit automático ao final, rollback em erro."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
