"""
GetRestaurant Use Case.

Retrieves a restaurant by ID.
"""

from uuid import UUID

from src.application.dto import RestaurantResponseDTO
from src.application.interfaces import IRestaurantRepository
from src.domain.exceptions import RestaurantNotFoundError


class GetRestaurantUseCase:
    """
    Use case for retrieving a restaurant by ID.

    Business flow:
    1. Fetch restaurant from repository
    2. If not found, raise exception
    3. Return DTO
    """

    def __init__(self, restaurant_repository: IRestaurantRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            restaurant_repository: Restaurant repository interface
        """
        self._restaurant_repository = restaurant_repository

    async def execute(self, restaurant_id: UUID) -> RestaurantResponseDTO:
        """
        Execute use case.

        Args:
            restaurant_id: ID of the restaurant to retrieve

        Returns:
            RestaurantResponseDTO: Restaurant data

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist
        """
        restaurant = await self._restaurant_repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise RestaurantNotFoundError(str(restaurant_id))

        return RestaurantResponseDTO.from_entity(restaurant)
