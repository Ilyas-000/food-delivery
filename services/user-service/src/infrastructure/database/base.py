"""SQLAlchemy base declarations and session factory helpers."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    SQLAlchemy 2.0 использует DeclarativeBase вместо declarative_base().
    Все модели наследуются от этого класса.

    Example:
        class UserModel(Base):
            __tablename__ = "users"
            ...
    """


# Database engine and session maker
# Будут настроены в dependency injection container
# Здесь только типы для type hints

AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def create_async_session_maker(database_url: str) -> async_sessionmaker[AsyncSession]:
    """
    Create async session maker for database.

    Args:
        database_url: PostgreSQL connection string
                     Format: postgresql+asyncpg://user:pass@host:port/db

    Returns:
        sessionmaker: Async session maker

    Example:
        session_maker = create_async_session_maker(
            "postgresql+asyncpg://user:pass@localhost:5432/user_db"
        )
        async with session_maker() as session:
            result = await session.execute(...)
    """
    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,  # Test connection before using
    )

    # Create session maker
    return async_sessionmaker(
        engine,
        expire_on_commit=False,  # Don't expire objects after commit
    )
