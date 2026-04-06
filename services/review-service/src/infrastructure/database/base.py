"""Database primitives for review-service."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base SQLAlchemy model class."""


AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def create_async_session_maker(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Create async SQLAlchemy session maker."""
    engine = create_async_engine(database_url, future=True, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)
