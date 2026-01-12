import pytest

from src.domain.value_objects.password import Password


@pytest.mark.unit()
def test_password_strips_whitespace() -> None:
    password = Password("  SecurePass123 ")

    assert password.value == "SecurePass123"


@pytest.mark.unit()
def test_password_requires_min_length() -> None:
    with pytest.raises(ValueError, match="at least 8 characters"):
        Password("Short1")


@pytest.mark.unit()
def test_password_requires_letter() -> None:
    with pytest.raises(ValueError, match="at least one letter"):
        Password("12345678")


@pytest.mark.unit()
def test_password_max_length() -> None:
    with pytest.raises(ValueError, match="must not exceed 72 characters"):
        Password("a" * 73)
