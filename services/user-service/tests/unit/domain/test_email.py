import pytest

from src.domain.value_objects.email import Email


@pytest.mark.unit()
def test_email_normalizes_case() -> None:
    email = Email("User@Example.COM")

    assert str(email) == "user@example.com"


@pytest.mark.unit()
def test_email_invalid_format_raises() -> None:
    with pytest.raises(ValueError, match="Invalid email format"):
        Email("not-an-email")


@pytest.mark.unit()
def test_email_equality_by_value() -> None:
    assert Email("user@example.com") == Email("user@example.com")
