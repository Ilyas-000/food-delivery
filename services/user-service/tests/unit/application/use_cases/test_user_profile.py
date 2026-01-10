from uuid import UUID

import pytest

from src.application.dto.user import GetUserProfileDTO, UpdateUserProfileDTO
from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.domain.entities.user import User
from src.domain.exceptions.base import InvalidProfileError, UserNotFoundError
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

BCRYPT_HASH = "$2b$12$" + "a" * 53


class FakeUserRepository(IUserRepository):
    def __init__(self, users: list[User]) -> None:
        self._by_id = {user.id: user for user in users}

    async def create(self, user: User) -> User:  # pragma: no cover - not used
        _ = user
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:  # pragma: no cover - not used
        _ = email
        raise NotImplementedError

    async def exists_by_email(self, email: Email) -> bool:  # pragma: no cover - not used
        _ = email
        raise NotImplementedError

    async def update(self, user: User) -> User:
        self._by_id[user.id] = user
        return user

    async def delete(self, user_id: UUID) -> None:  # pragma: no cover - not used
        _ = user_id
        raise NotImplementedError


@pytest.mark.asyncio()
async def test_get_user_profile_success() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    repo = FakeUserRepository([user])
    use_case = GetUserProfileUseCase(repo)

    result = await use_case.execute(GetUserProfileDTO(user_id=user.id))

    assert result.id == user.id
    assert result.email == "user@example.com"


@pytest.mark.asyncio()
async def test_get_user_profile_not_found() -> None:
    repo = FakeUserRepository([])
    use_case = GetUserProfileUseCase(repo)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(GetUserProfileDTO(user_id=UUID(int=0)))


@pytest.mark.asyncio()
async def test_update_user_profile_success() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
        phone="+12345678901",
    )
    repo = FakeUserRepository([user])
    use_case = UpdateUserProfileUseCase(repo)

    result = await use_case.execute(
        UpdateUserProfileDTO(
            user_id=user.id,
            full_name="Jane Doe",
            phone="+10987654321",
        )
    )

    assert result.full_name == "Jane Doe"
    assert result.phone == "+10987654321"


@pytest.mark.asyncio()
async def test_update_user_profile_no_fields() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    repo = FakeUserRepository([user])
    use_case = UpdateUserProfileUseCase(repo)

    with pytest.raises(InvalidProfileError):
        await use_case.execute(UpdateUserProfileDTO(user_id=user.id))


@pytest.mark.asyncio()
async def test_update_user_profile_invalid_phone() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    repo = FakeUserRepository([user])
    use_case = UpdateUserProfileUseCase(repo)

    with pytest.raises(InvalidProfileError):
        await use_case.execute(
            UpdateUserProfileDTO(
                user_id=user.id,
                phone="123",
            )
        )
