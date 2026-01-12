import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.exceptions.base import UserAlreadyExistsError
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole
from src.infrastructure.database.repositories.user_repository import UserRepository

BCRYPT_HASH = "$2b$12$" + "a" * 53


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_user_repository_create_and_get(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )

    created = await repo.create(user)
    fetched_by_id = await repo.get_by_id(created.id)
    fetched_by_email = await repo.get_by_email(created.email)

    assert fetched_by_id is not None
    assert fetched_by_email is not None
    assert fetched_by_id.id == created.id
    assert fetched_by_email.email == created.email


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_user_repository_exists_by_email(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    email = Email("user@example.com")

    assert await repo.exists_by_email(email) is False

    user = User.create(
        email=email,
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    await repo.create(user)

    assert await repo.exists_by_email(email) is True


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_user_repository_duplicate_email(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    email = Email("user@example.com")

    user = User.create(
        email=email,
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    await repo.create(user)

    duplicate_user = User.create(
        email=email,
        password_hash=BCRYPT_HASH,
        full_name="Jane Doe",
        role=UserRole.CUSTOMER,
    )

    with pytest.raises(UserAlreadyExistsError):
        await repo.create(duplicate_user)


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_user_repository_update(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
        phone="+12345678901",
    )
    created = await repo.create(user)

    created.update_profile(full_name="Jane Doe", phone="+10987654321")
    updated = await repo.update(created)

    assert updated.full_name == "Jane Doe"
    assert updated.phone == "+10987654321"
