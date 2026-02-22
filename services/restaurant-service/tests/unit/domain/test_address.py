"""Unit tests for Address value object."""

import pytest

from src.domain.value_objects.address import Address


@pytest.mark.unit()
def test_address_creation() -> None:
    """Test address creation with valid data."""
    address = Address(
        street="123 Main St",
        city="New York",
        postal_code="10001",
    )

    assert address.street == "123 Main St"
    assert address.city == "New York"
    assert address.postal_code == "10001"


@pytest.mark.unit()
def test_address_with_invalid_street_raises_error() -> None:
    """Test address creation with invalid street raises ValueError."""
    with pytest.raises(ValueError, match="Street must be at least"):
        Address(street="", city="New York", postal_code="10001")


@pytest.mark.unit()
def test_address_with_invalid_city_raises_error() -> None:
    """Test address creation with invalid city raises ValueError."""
    with pytest.raises(ValueError, match="City must be at least"):
        Address(street="123 Main St", city="", postal_code="10001")


@pytest.mark.unit()
def test_address_with_invalid_postal_code_raises_error() -> None:
    """Test address creation with invalid postal code raises ValueError."""
    with pytest.raises(ValueError, match="Postal code must be at least"):
        Address(street="123 Main St", city="New York", postal_code="")


@pytest.mark.unit()
def test_address_equality() -> None:
    """Test address equality by value."""
    address1 = Address(street="123 Main St", city="New York", postal_code="10001")
    address2 = Address(street="123 Main St", city="New York", postal_code="10001")

    assert address1 == address2


@pytest.mark.unit()
def test_address_inequality() -> None:
    """Test address inequality."""
    address1 = Address(street="123 Main St", city="New York", postal_code="10001")
    address2 = Address(street="456 Elm St", city="Brooklyn", postal_code="11201")

    assert address1 != address2
