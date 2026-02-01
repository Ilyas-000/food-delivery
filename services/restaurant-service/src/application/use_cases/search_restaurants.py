"""
SearchRestaurants Use Case.

Searches for restaurants based on filters.
"""

from src.application.dto import RestaurantResponseDTO, SearchRestaurantsDTO
from src.application.interfaces import IRestaurantRepository


class SearchRestaurantsUseCase:
    """
    Use case for searching restaurants.

    Business flow:
    1. Pass search filters to repository
    2. Convert entities to DTOs
    3. Return list of DTOs
    """

    def __init__(self, restaurant_repository: IRestaurantRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            restaurant_repository: Restaurant repository interface
        """
        self._restaurant_repository = restaurant_repository

    async def execute(self, dto: SearchRestaurantsDTO) -> list[RestaurantResponseDTO]:
        """
        Execute use case.

        Args:
            dto: Search filters

        Returns:
            list[RestaurantResponseDTO]: List of matching restaurants
        """
        restaurants = await self._restaurant_repository.search(
            cuisine=dto.cuisine,
            city=dto.city,
            min_rating=dto.min_rating,
            is_active=dto.is_active,
            limit=dto.limit,
            offset=dto.offset,
        )

        return [RestaurantResponseDTO.from_entity(restaurant) for restaurant in restaurants]
