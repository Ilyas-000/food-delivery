"""
Authentication dependencies for FastAPI endpoints.

Provides password hashing, token service, auth use cases, and current user resolution.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.login_user import LoginUserUseCase
from src.application.use_cases.refresh_token import RefreshTokenUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.config import settings
from src.domain.entities.user import User
from src.domain.exceptions.base import InvalidTokenError
from src.infrastructure.security.password_hasher import PasswordHasher
from src.infrastructure.security.token_service import TokenService
from src.interface.dependencies.database import get_user_repository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_password_hasher() -> IPasswordHasher:
    """Provide password hasher implementation."""
    return PasswordHasher(rounds=settings.password_bcrypt_rounds)


async def get_token_service() -> ITokenService:
    """Provide token service implementation."""
    return TokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_expires_minutes=settings.jwt_access_token_expire_minutes,
        refresh_expires_days=settings.jwt_refresh_token_expire_days,
    )


async def get_register_user_use_case(
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> RegisterUserUseCase:
    """Provide RegisterUserUseCase."""
    return RegisterUserUseCase(
        user_repository=repository,
        password_hasher=password_hasher,
    )


async def get_login_user_use_case(
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> LoginUserUseCase:
    """Provide LoginUserUseCase."""
    return LoginUserUseCase(
        user_repository=repository,
        password_hasher=password_hasher,
        token_service=token_service,
    )


async def get_refresh_token_use_case(
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> RefreshTokenUseCase:
    """Provide RefreshTokenUseCase."""
    return RefreshTokenUseCase(
        user_repository=repository,
        token_service=token_service,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> User:
    """
    Resolve current user from Authorization header.

    Raises:
        InvalidTokenError: If token is missing, invalid, or user not found.
    """
    if credentials is None or not credentials.credentials:
        raise InvalidTokenError("Missing access token")

    payload = token_service.decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise InvalidTokenError("Invalid token type")

    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Missing subject")

    try:
        user_id = UUID(str(subject))
    except ValueError as exc:
        raise InvalidTokenError("Invalid subject") from exc

    user = await repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    return user
