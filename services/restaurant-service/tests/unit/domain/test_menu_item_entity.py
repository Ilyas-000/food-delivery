"""Unit tests for MenuItem entity."""

from datetime import UTC
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.domain.entities.menu_item import MenuItem
from src.domain.value_objects.availability import Availability
from src.domain.value_objects.category import Category
from src.domain.value_objects.price import Price


@pytest.mark.unit()
def test_menu_item_create_sets_defaults() -> None:
    """Test menu item creation sets default values."""
    restaurant_id = uuid4()
    price = Price(amount=Decimal("15.99"))

    menu_item = MenuItem.create(
        restaurant_id=restaurant_id,
        name="Margherita Pizza",
        description="Classic Italian pizza",
        price=price,
        category=Category.MAIN_COURSE,
    )

    assert isinstance(menu_item.id, UUID)
    assert menu_item.restaurant_id == restaurant_id
    assert menu_item.name == "Margherita Pizza"
    assert menu_item.price == price
    assert menu_item.availability == Availability.AVAILABLE
    assert menu_item.is_available is True
    assert menu_item.image_url is None
    assert menu_item.created_at.tzinfo == UTC
    assert menu_item.updated_at.tzinfo == UTC


@pytest.mark.unit()
def test_menu_item_create_with_invalid_name_raises_error() -> None:
    """Test menu item creation with invalid name raises ValueError."""
    restaurant_id = uuid4()
    price = Price(amount=Decimal("15.99"))

    with pytest.raises(Exception, match="Invalid name"):
        MenuItem.create(
            restaurant_id=restaurant_id,
            name="A",
            description="Test",
            price=price,
            category=Category.MAIN_COURSE,
        )


@pytest.mark.unit()
def test_menu_item_create_with_image_url() -> None:
    """Test menu item creation with image URL."""
    menu_item = MenuItem.create(
        restaurant_id=uuid4(),
        name="Margherita Pizza",
        description="Classic Italian pizza",
        price=Price(amount=Decimal("15.99")),
        category=Category.MAIN_COURSE,
        image_url="https://example.com/pizza.jpg",
    )

    assert menu_item.image_url == "https://example.com/pizza.jpg"


@pytest.mark.unit()
def test_menu_item_update_info() -> None:
    """Test updating menu item information."""
    menu_item = MenuItem.create(
        restaurant_id=uuid4(),
        name="Original Name",
        description="Original description",
        price=Price(amount=Decimal("10.00")),
        category=Category.APPETIZER,
    )
    previous_updated_at = menu_item.updated_at

    new_price = Price(amount=Decimal("12.50"))
    menu_item.update_info(
        name="Updated Name",
        description="Updated description",
        price=new_price,
        category=Category.MAIN_COURSE,
        image_url="https://example.com/new.jpg",
    )

    assert menu_item.name == "Updated Name"
    assert menu_item.description == "Updated description"
    assert menu_item.price == new_price
    assert menu_item.category == Category.MAIN_COURSE
    assert menu_item.image_url == "https://example.com/new.jpg"
    assert menu_item.updated_at >= previous_updated_at


@pytest.mark.unit()
def test_menu_item_make_available_unavailable() -> None:
    """Test making menu item available and unavailable."""
    menu_item = MenuItem.create(
        restaurant_id=uuid4(),
        name="Pizza",
        description="Test",
        price=Price(amount=Decimal("15.99")),
        category=Category.MAIN_COURSE,
    )

    assert menu_item.availability == Availability.AVAILABLE

    menu_item.mark_unavailable()
    assert menu_item.availability == Availability.OUT_OF_STOCK

    menu_item.mark_available()
    assert menu_item.availability == Availability.AVAILABLE


@pytest.mark.unit()
def test_menu_item_equality_by_id() -> None:
    """Test menu item equality is based on ID."""
    item_id = uuid4()
    restaurant_id = uuid4()
    price = Price(amount=Decimal("15.99"))

    item1 = MenuItem(
        id=item_id,
        restaurant_id=restaurant_id,
        name="Item 1",
        description="Test 1",
        price=price,
        category=Category.MAIN_COURSE,
        image_url=None,
        availability=Availability.AVAILABLE,
    )

    item2 = MenuItem(
        id=item_id,
        restaurant_id=restaurant_id,
        name="Item 2",
        description="Test 2",
        price=price,
        category=Category.DESSERT,
        image_url=None,
        availability=Availability.OUT_OF_STOCK,
    )

    assert item1 == item2
