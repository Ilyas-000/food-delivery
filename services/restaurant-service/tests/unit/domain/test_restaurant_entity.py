"""Unit tests for Restaurant entity."""

from datetime import UTC
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.domain.entities.restaurant import Restaurant
from src.domain.exceptions.restaurant import InvalidRestaurantDataError
from src.domain.value_objects.address import Address
from src.domain.value_objects.cuisine import Cuisine


@pytest.mark.unit()
def test_restaurant_create_sets_defaults() -> None:
    """Test restaurant creation sets default values."""
    owner_id = uuid4()
    address = Address(
        street="123 Main St",
        city="New York",
        postal_code="10001",
        latitude=40.7128,
        longitude=-74.0060,
    )

    restaurant = Restaurant.create(
        owner_id=owner_id,
        name="Test Restaurant",
        description="A test restaurant",
        address=address,
        cuisine=Cuisine.ITALIAN,
    )

    assert isinstance(restaurant.id, UUID)
    assert restaurant.owner_id == owner_id
    assert restaurant.name == "Test Restaurant"
    assert restaurant.is_active is True
    assert restaurant.rating == Decimal("0.0")
    assert restaurant.created_at.tzinfo == UTC
    assert restaurant.updated_at.tzinfo == UTC


@pytest.mark.unit()
def test_restaurant_create_with_invalid_name_raises_error() -> None:
    """Test restaurant creation with invalid name raises domain error."""
    owner_id = uuid4()
    address = Address(street="123 Main St", city="New York", postal_code="10001")

    with pytest.raises(InvalidRestaurantDataError, match="Invalid name"):
        Restaurant.create(
            owner_id=owner_id,
            name="A",
            description="Test",
            address=address,
            cuisine=Cuisine.ITALIAN,
        )


@pytest.mark.unit()
def test_restaurant_update_info() -> None:
    """Test updating restaurant information."""
    restaurant = Restaurant.create(
        owner_id=uuid4(),
        name="Original Name",
        description="Original description",
        address=Address(street="123 Main St", city="New York", postal_code="10001"),
        cuisine=Cuisine.ITALIAN,
    )
    previous_updated_at = restaurant.updated_at

    new_address = Address(street="456 Elm St", city="Brooklyn", postal_code="11201")
    restaurant.update_info(
        name="Updated Name",
        description="Updated description",
        address=new_address,
        cuisine=Cuisine.CHINESE,
    )

    assert restaurant.name == "Updated Name"
    assert restaurant.description == "Updated description"
    assert restaurant.address == new_address
    assert restaurant.cuisine == Cuisine.CHINESE
    assert restaurant.updated_at >= previous_updated_at


@pytest.mark.unit()
def test_restaurant_activate_deactivate() -> None:
    """Test restaurant activation and deactivation."""
    restaurant = Restaurant.create(
        owner_id=uuid4(),
        name="Test Restaurant",
        description="Test",
        address=Address(street="123 Main St", city="New York", postal_code="10001"),
        cuisine=Cuisine.ITALIAN,
    )

    assert restaurant.is_active is True

    restaurant.deactivate()
    assert restaurant.is_active is False

    restaurant.activate()
    assert restaurant.is_active is True


@pytest.mark.unit()
def test_restaurant_update_rating() -> None:
    """Test updating restaurant rating."""
    restaurant = Restaurant.create(
        owner_id=uuid4(),
        name="Test Restaurant",
        description="Test",
        address=Address(street="123 Main St", city="New York", postal_code="10001"),
        cuisine=Cuisine.ITALIAN,
    )

    restaurant.update_rating(Decimal("4.5"))

    assert restaurant.rating == Decimal("4.5")


@pytest.mark.unit()
def test_restaurant_equality_by_id() -> None:
    """Test restaurant equality is based on ID."""
    restaurant_id = uuid4()
    owner_id = uuid4()
    address = Address(street="123 Main St", city="New York", postal_code="10001")

    restaurant1 = Restaurant(
        id=restaurant_id,
        owner_id=owner_id,
        name="Restaurant 1",
        description="Test",
        address=address,
        cuisine=Cuisine.ITALIAN,
        rating=Decimal("0.0"),
        is_active=True,
    )

    restaurant2 = Restaurant(
        id=restaurant_id,
        owner_id=owner_id,
        name="Restaurant 2",
        description="Different",
        address=address,
        cuisine=Cuisine.CHINESE,
        rating=Decimal("0.0"),
        is_active=True,
    )

    assert restaurant1 == restaurant2
