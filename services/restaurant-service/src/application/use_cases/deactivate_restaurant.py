"""DeactivateRestaurant use case."""

from uuid import UUID

from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.domain.exceptions.restaurant import RestaurantNotFoundError


class DeactivateRestaurantUseCase:
    """Deactivate restaurant (soft delete)."""

    def __init__(self, restaurant_repository: IRestaurantRepository) -> None:
        self._restaurant_repository = restaurant_repository

    async def execute(self, restaurant_id: UUID) -> None:
        restaurant = await self._restaurant_repository.get_by_id(restaurant_id)
        if restaurant is None:
            raise RestaurantNotFoundError(str(restaurant_id))

        restaurant.deactivate()
        await self._restaurant_repository.update(restaurant)
