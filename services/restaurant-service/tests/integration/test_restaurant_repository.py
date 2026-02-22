"""Integration tests for RestaurantRepository."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.restaurant import Restaurant
from src.domain.value_objects.address import Address
from src.domain.value_objects.cuisine import Cuisine
from src.infrastructure.database.repositories.restaurant_repository import (
    RestaurantRepository,
)


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_restaurant_repository_create_and_get(db_session: AsyncSession) -> None:
    """Test creating and retrieving a restaurant."""
    repo = RestaurantRepository(db_session)
    owner_id = uuid4()

    restaurant = Restaurant.create(
        owner_id=owner_id,
        name="Test Restaurant",
        description="A test restaurant",
        address=Address(street="123 Main St", city="New York", postal_code="10001"),
        cuisine=Cuisine.ITALIAN,
    )

    created = await repo.create(restaurant)
    fetched_by_id = await repo.get_by_id(created.id)
    fetched_by_owner = await repo.get_by_owner_id(owner_id)

    assert fetched_by_id is not None
    assert fetched_by_id.id == created.id
    assert fetched_by_id.name == "Test Restaurant"
    assert len(fetched_by_owner) == 1
    assert fetched_by_owner[0].owner_id == owner_id


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_restaurant_repository_get_by_owner_and_name(db_session: AsyncSession) -> None:
    """Test get restaurant by owner and name."""
    repo = RestaurantRepository(db_session)
    owner_id = uuid4()

    created = await repo.create(
        Restaurant.create(
            owner_id=owner_id,
            name="First Restaurant",
            description="Test",
            address=Address(street="123 Main St", city="New York", postal_code="10001"),
            cuisine=Cuisine.ITALIAN,
        )
    )

    found = await repo.get_by_owner_and_name(owner_id, "First Restaurant")
    missing = await repo.get_by_owner_and_name(owner_id, "Unknown")

    assert found is not None
    assert found.id == created.id
    assert missing is None


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_restaurant_repository_update(db_session: AsyncSession) -> None:
    """Test updating a restaurant."""
    repo = RestaurantRepository(db_session)

    restaurant = Restaurant.create(
        owner_id=uuid4(),
        name="Original Name",
        description="Original description",
        address=Address(street="123 Main St", city="New York", postal_code="10001"),
        cuisine=Cuisine.ITALIAN,
    )
    created = await repo.create(restaurant)

    new_address = Address(street="456 Elm St", city="Brooklyn", postal_code="11201")
    created.update_info(
        name="Updated Name",
        description="Updated description",
        address=new_address,
        cuisine=Cuisine.CHINESE,
    )
    updated = await repo.update(created)

    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"
    assert updated.address == new_address
    assert updated.cuisine == Cuisine.CHINESE


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_restaurant_repository_search_filters(db_session: AsyncSession) -> None:
    """Test searching restaurants by cuisine, city and rating."""
    repo = RestaurantRepository(db_session)

    italian = Restaurant.create(
        owner_id=uuid4(),
        name="Italian Restaurant",
        description="Test",
        address=Address(street="123 Main St", city="New York", postal_code="10001"),
        cuisine=Cuisine.ITALIAN,
    )
    italian.update_rating(Decimal("4.5"))

    chinese = Restaurant.create(
        owner_id=uuid4(),
        name="Chinese Restaurant",
        description="Test",
        address=Address(street="456 Elm St", city="Brooklyn", postal_code="11201"),
        cuisine=Cuisine.CHINESE,
    )
    chinese.update_rating(Decimal("2.5"))

    await repo.create(italian)
    await repo.create(chinese)

    cuisine_results = await repo.search(cuisine=Cuisine.ITALIAN)
    city_results = await repo.search(city="New York")
    rating_results = await repo.search(min_rating=4.0)

    assert len(cuisine_results) == 1
    assert cuisine_results[0].name == "Italian Restaurant"

    assert len(city_results) == 1
    assert city_results[0].address.city == "New York"

    assert len(rating_results) == 1
    assert rating_results[0].rating >= Decimal("4.0")


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_restaurant_repository_delete_is_soft(db_session: AsyncSession) -> None:
    """Test delete performs soft-delete by setting is_active=False."""
    repo = RestaurantRepository(db_session)

    created = await repo.create(
        Restaurant.create(
            owner_id=uuid4(),
            name="To Delete",
            description="Test",
            address=Address(street="123 Main St", city="New York", postal_code="10001"),
            cuisine=Cuisine.ITALIAN,
        )
    )

    await repo.delete(created.id)

    deleted = await repo.get_by_id(created.id)
    assert deleted is not None
    assert deleted.is_active is False
