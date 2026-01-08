"""
Database dependencies for dependency injection.

FastAPI Depends() pattern for providing database sessions and repositories.

Interview note:
Dependency Injection allows:
- Easy testing (mock repositories)
- Loose coupling
- Single responsibility (endpoints don't manage DB lifecycle)
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.register_user import RegisterUserUseCase
from src.config import settings
from src.infrastructure.database import base
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.security.password_hasher import PasswordHasher


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides database session.

    Yields database session and ensures it's closed after request.
    This is FastAPI pattern for resource management.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session)):
            # Use session
            pass
        # Session automatically closed after request
    """
    if base.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call create_async_session_maker() first.")

    async with base.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IUserRepository:
    """
    Dependency that provides UserRepository.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        IUserRepository: User repository implementation

    Example:
        @app.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            repo: IUserRepository = Depends(get_user_repository)
        ):
            user = await repo.get_by_id(user_id)
            return user
    """
    return UserRepository(session)


async def get_password_hasher() -> IPasswordHasher:
    """
    Dependency that provides PasswordHasher.

    Returns:
        IPasswordHasher: Password hasher implementation

    Note: This is stateless service, can be reused.
    In production, might use singleton pattern.

    Example:
        @app.post("/auth/change-password")
        async def change_password(
            hasher: IPasswordHasher = Depends(get_password_hasher)
        ):
            hashed = await hasher.hash_password(new_password)
            ...
    """
    # PasswordHasher is stateless, safe to create new instance
    return PasswordHasher(rounds=settings.password_bcrypt_rounds)


async def get_register_user_use_case(
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> RegisterUserUseCase:
    """
    Dependency that provides RegisterUserUseCase.

    This is higher-level dependency that composes other dependencies.
    Demonstrates Dependency Inversion Principle - use case depends on
    abstractions (interfaces), not concrete implementations.

    Args:
        repository: User repository (injected)
        password_hasher: Password hasher (injected)

    Returns:
        RegisterUserUseCase: Configured use case

    Example:
        @app.post("/auth/register")
        async def register(
            use_case: RegisterUserUseCase = Depends(get_register_user_use_case)
        ):
            result = await use_case.execute(dto)
            return result
    """
    return RegisterUserUseCase(
        user_repository=repository,
        password_hasher=password_hasher,
    )
