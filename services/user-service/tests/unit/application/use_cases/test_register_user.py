from uuid import UUID

import pytest

from src.application.dto.auth import RegisterUserDTO
from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.entities.user import User
from src.domain.exceptions.base import (
    InvalidEmailError,
    InvalidPasswordError,
    UserAlreadyExistsError,
)
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

BCRYPT_HASH = "$2b$12$" + "a" * 53


class FakeUserRepository(IUserRepository):
    def __init__(self, existing_emails: set[str] | None = None) -> None:
        self._existing_emails = existing_emails or set()
        self.created: list[User] = []

    async def create(self, user: User) -> User:
        self.created.append(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:  # pragma: no cover
        _ = user_id
        raise NotImplementedError

    async def get_by_email(self, email: Email) -> User | None:  # pragma: no cover
        _ = email
        raise NotImplementedError

    async def exists_by_email(self, email: Email) -> bool:
        return str(email) in self._existing_emails

    async def update(self, user: User) -> User:  # pragma: no cover
        _ = user
        raise NotImplementedError

    async def delete(self, user_id: UUID) -> None:  # pragma: no cover
        _ = user_id
        raise NotImplementedError


class FakePasswordHasher(IPasswordHasher):
    def __init__(self, hashed: str) -> None:
        self._hashed = hashed
        self.seen_plaintext: list[str] = []

    async def hash_password(self, plain_password: str) -> str:
        self.seen_plaintext.append(plain_password)
        return self._hashed

    async def verify_password(  # pragma: no cover - not used in tests
        self, plain_password: str, password_hash: str
    ) -> bool:
        _ = plain_password
        _ = password_hash
        raise NotImplementedError


@pytest.mark.asyncio()
@pytest.mark.unit()
async def test_register_user_success() -> None:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher(BCRYPT_HASH)
    use_case = RegisterUserUseCase(repo, hasher)

    result = await use_case.execute(
        RegisterUserDTO(
            email="user@example.com",
            password="SecurePass123",
            full_name="John Doe",
            role=UserRole.CUSTOMER,
        )
    )

    assert result.email == "user@example.com"
    assert repo.created[0].password_hash == BCRYPT_HASH
    assert hasher.seen_plaintext == ["SecurePass123"]


@pytest.mark.asyncio()
@pytest.mark.unit()
async def test_register_user_invalid_email() -> None:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher(BCRYPT_HASH)
    use_case = RegisterUserUseCase(repo, hasher)

    with pytest.raises(InvalidEmailError):
        await use_case.execute(
            RegisterUserDTO(
                email="not-an-email",
                password="SecurePass123",
                full_name="John Doe",
                role=UserRole.CUSTOMER,
            )
        )

    assert repo.created == []


@pytest.mark.asyncio()
@pytest.mark.unit()
async def test_register_user_invalid_password() -> None:
    repo = FakeUserRepository()
    hasher = FakePasswordHasher(BCRYPT_HASH)
    use_case = RegisterUserUseCase(repo, hasher)

    with pytest.raises(InvalidPasswordError):
        await use_case.execute(
            RegisterUserDTO(
                email="user@example.com",
                password="12345678",
                full_name="John Doe",
                role=UserRole.CUSTOMER,
            )
        )

    assert repo.created == []


@pytest.mark.asyncio()
@pytest.mark.unit()
async def test_register_user_duplicate_email() -> None:
    repo = FakeUserRepository(existing_emails={"user@example.com"})
    hasher = FakePasswordHasher(BCRYPT_HASH)
    use_case = RegisterUserUseCase(repo, hasher)

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            RegisterUserDTO(
                email="user@example.com",
                password="SecurePass123",
                full_name="John Doe",
                role=UserRole.CUSTOMER,
            )
        )

    assert repo.created == []
