"""SQLAlchemy base declarations and session factory helpers."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def create_async_session_maker(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create async SQLAlchemy session maker."""
    engine = create_async_engine(
        database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
    )

    return async_sessionmaker(engine, expire_on_commit=False)
