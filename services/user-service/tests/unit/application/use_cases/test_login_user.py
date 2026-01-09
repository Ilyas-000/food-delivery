from typing import Any
from uuid import UUID

import pytest

from src.application.dto.auth import AuthTokensDTO, LoginUserDTO
from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.login_user import LoginUserUseCase
from src.domain.entities.user import User
from src.domain.exceptions.base import InvalidCredentialsError, InvalidEmailError
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

BCRYPT_HASH = "$2b$12$" + "a" * 53


class FakeUserRepository(IUserRepository):
    def __init__(self, users: list[User]) -> None:
        self._by_email = {str(user.email): user for user in users}

    async def create(self, user: User) -> User:  # pragma: no cover - not used in tests
        _ = user
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID) -> User | None:  # pragma: no cover - not used
        _ = user_id
        raise NotImplementedError

    async def get_by_email(self, email: Email) -> User | None:
        return self._by_email.get(str(email))

    async def exists_by_email(self, email: Email) -> bool:  # pragma: no cover - not used in tests
        return str(email) in self._by_email

    async def update(self, user: User) -> User:  # pragma: no cover - not used in tests
        _ = user
        raise NotImplementedError

    async def delete(self, user_id: UUID) -> None:  # pragma: no cover - not used in tests
        _ = user_id
        raise NotImplementedError


class FakePasswordHasher(IPasswordHasher):
    def __init__(self, expected_password: str) -> None:
        self._expected_password = expected_password

    async def hash_password(
        self, plain_password: str
    ) -> str:  # pragma: no cover - not used in tests
        _ = plain_password
        raise NotImplementedError

    async def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return plain_password == self._expected_password and password_hash == BCRYPT_HASH


class FakeTokenService(ITokenService):
    def __init__(self, tokens: AuthTokensDTO) -> None:
        self._tokens = tokens

    def create_token_pair(
        self,
        subject: str,
        role: UserRole,
        extra_claims: dict[str, Any] | None = None,
    ) -> AuthTokensDTO:
        _ = subject
        _ = role
        if extra_claims:
            _ = extra_claims
        return self._tokens

    def decode_token(self, token: str) -> dict[str, Any]:  # pragma: no cover - not used
        _ = token
        raise NotImplementedError


@pytest.mark.asyncio()
async def test_login_user_success() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )

    repo = FakeUserRepository([user])
    hasher = FakePasswordHasher(expected_password="Secret123")
    token_service = FakeTokenService(
        AuthTokensDTO(
            access_token="access",
            refresh_token="refresh",
            token_type="bearer",
            access_expires_in=1800,
            refresh_expires_in=604800,
        )
    )
    use_case = LoginUserUseCase(repo, hasher, token_service)

    result = await use_case.execute(LoginUserDTO(email="user@example.com", password="Secret123"))

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"


@pytest.mark.asyncio()
async def test_login_user_invalid_password() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )

    repo = FakeUserRepository([user])
    hasher = FakePasswordHasher(expected_password="CorrectPassword")
    token_service = FakeTokenService(
        AuthTokensDTO(
            access_token="access",
            refresh_token="refresh",
            token_type="bearer",
            access_expires_in=1800,
            refresh_expires_in=604800,
        )
    )
    use_case = LoginUserUseCase(repo, hasher, token_service)

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(LoginUserDTO(email="user@example.com", password="WrongPassword"))


@pytest.mark.asyncio()
async def test_login_user_invalid_email() -> None:
    repo = FakeUserRepository([])
    hasher = FakePasswordHasher(expected_password="Secret123")
    token_service = FakeTokenService(
        AuthTokensDTO(
            access_token="access",
            refresh_token="refresh",
            token_type="bearer",
            access_expires_in=1800,
            refresh_expires_in=604800,
        )
    )
    use_case = LoginUserUseCase(repo, hasher, token_service)

    with pytest.raises(InvalidEmailError):
        await use_case.execute(LoginUserDTO(email="not-an-email", password="Secret123"))
