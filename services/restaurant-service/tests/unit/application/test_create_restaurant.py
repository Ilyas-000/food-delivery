"""Unit tests for CreateRestaurantUseCase."""

from uuid import UUID, uuid4

import pytest

from src.application.dto.restaurant_dto import CreateRestaurantDTO
from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.application.use_cases.create_restaurant import CreateRestaurantUseCase
from src.domain.entities.restaurant import Restaurant
from src.domain.exceptions.restaurant import RestaurantAlreadyExistsError
from src.domain.value_objects.address import Address
from src.domain.value_objects.cuisine import Cuisine


class FakeRestaurantRepository(IRestaurantRepository):
    """Fake repository for testing."""

    def __init__(self, duplicate_exists: bool = False) -> None:
        self._duplicate_exists = duplicate_exists
        self.created: list[Restaurant] = []

    async def create(self, restaurant: Restaurant) -> Restaurant:
        self.created.append(restaurant)
        return restaurant

    async def get_by_id(self, restaurant_id: UUID) -> Restaurant | None:  # pragma: no cover
        _ = restaurant_id
        return None

    async def get_by_owner_and_name(self, owner_id: UUID, name: str) -> Restaurant | None:
        if self._duplicate_exists:
            return Restaurant.create(
                owner_id=owner_id,
                name=name,
                description="Existing restaurant",
                address=Address(street="123 Main St", city="New York", postal_code="10001"),
                cuisine=Cuisine.ITALIAN,
            )
        return None

    async def update(self, restaurant: Restaurant) -> Restaurant:  # pragma: no cover
        return restaurant

    async def delete(self, restaurant_id: UUID) -> None:  # pragma: no cover
        _ = restaurant_id

    async def search(  # pragma: no cover
        self,
        cuisine: Cuisine | None = None,
        city: str | None = None,
        min_rating: float | None = None,
        is_active: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Restaurant]:
        _ = (cuisine, city, min_rating, is_active, limit, offset)
        return []

    async def get_by_owner_id(self, owner_id: UUID) -> list[Restaurant]:  # pragma: no cover
        _ = owner_id
        return []


@pytest.mark.asyncio()
@pytest.mark.unit()
async def test_create_restaurant_success() -> None:
    """Test successful restaurant creation."""
    repo = FakeRestaurantRepository()
    use_case = CreateRestaurantUseCase(repo)

    dto = CreateRestaurantDTO(
        owner_id=uuid4(),
        name="Test Restaurant",
        description="A test restaurant",
        street="123 Main St",
        city="New York",
        postal_code="10001",
        latitude=40.7128,
        longitude=-74.0060,
        cuisine=Cuisine.ITALIAN,
    )

    result = await use_case.execute(dto)

    assert result.name == "Test Restaurant"
    assert result.cuisine == Cuisine.ITALIAN
    assert len(repo.created) == 1
    assert repo.created[0].owner_id == dto.owner_id


@pytest.mark.asyncio()
@pytest.mark.unit()
async def test_create_restaurant_duplicate_name_for_owner() -> None:
    """Test duplicate restaurant name for the same owner."""
    owner_id = uuid4()
    repo = FakeRestaurantRepository(duplicate_exists=True)
    use_case = CreateRestaurantUseCase(repo)

    dto = CreateRestaurantDTO(
        owner_id=owner_id,
        name="Test Restaurant",
        description="Test",
        street="456 Elm St",
        city="Brooklyn",
        postal_code="11201",
        latitude=40.6782,
        longitude=-73.9442,
        cuisine=Cuisine.CHINESE,
    )

    with pytest.raises(RestaurantAlreadyExistsError, match="already exists"):
        await use_case.execute(dto)

    assert len(repo.created) == 0
