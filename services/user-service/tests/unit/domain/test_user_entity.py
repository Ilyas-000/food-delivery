from datetime import UTC
from uuid import UUID

import pytest

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

BCRYPT_HASH = "$2b$12$" + "a" * 53


@pytest.mark.unit()
def test_user_create_sets_defaults() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )

    assert isinstance(user.id, UUID)
    assert user.is_active is True
    assert user.phone is None
    assert user.created_at.tzinfo == UTC
    assert user.updated_at.tzinfo == UTC


@pytest.mark.unit()
def test_user_create_invalid_full_name() -> None:
    with pytest.raises(ValueError, match="Full name must be at least"):
        User.create(
            email=Email("user@example.com"),
            password_hash=BCRYPT_HASH,
            full_name="A",
            role=UserRole.CUSTOMER,
        )


@pytest.mark.unit()
def test_user_create_invalid_password_hash() -> None:
    with pytest.raises(ValueError, match="Invalid password hash format"):
        User.create(
            email=Email("user@example.com"),
            password_hash="invalid-hash",
            full_name="John Doe",
            role=UserRole.CUSTOMER,
        )


@pytest.mark.unit()
def test_user_update_profile_updates_fields() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    previous_updated_at = user.updated_at

    user.update_profile(full_name="Jane Doe", phone="+12345678901")

    assert user.full_name == "Jane Doe"
    assert user.phone == "+12345678901"
    assert user.updated_at >= previous_updated_at


@pytest.mark.unit()
def test_user_activation_flags() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )

    user.deactivate()
    assert user.is_active is False

    user.activate()
    assert user.is_active is True


@pytest.mark.unit()
def test_user_equality_by_id() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    other_user = User(
        id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    assert user == other_user


@pytest.mark.unit()
def test_user_to_dict_hides_password_hash() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )

    payload = user.to_dict()

    assert "password_hash" not in payload
    assert payload["email"] == "user@example.com"
    assert payload["role"] == "customer"
