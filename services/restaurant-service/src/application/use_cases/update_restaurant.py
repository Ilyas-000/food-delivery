"""
UpdateRestaurant Use Case.

Updates restaurant information.
"""

from uuid import UUID

from src.application.dto.restaurant_dto import RestaurantResponseDTO, UpdateRestaurantDTO
from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.domain.exceptions.restaurant import RestaurantNotFoundError
from src.domain.value_objects.address import Address


class UpdateRestaurantUseCase:
    """
    Use case for updating restaurant information.

    Business flow:
    1. Fetch restaurant from repository
    2. If not found, raise exception
    3. Create new Address if address fields provided
    4. Update restaurant entity (validates business rules)
    5. Save to repository
    6. Return DTO
    """

    def __init__(self, restaurant_repository: IRestaurantRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            restaurant_repository: Restaurant repository interface
        """
        self._restaurant_repository = restaurant_repository

    async def execute(self, restaurant_id: UUID, dto: UpdateRestaurantDTO) -> RestaurantResponseDTO:
        """
        Execute use case.

        Args:
            restaurant_id: ID of the restaurant to update
            dto: Update data

        Returns:
            RestaurantResponseDTO: Updated restaurant

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist
            InvalidRestaurantDataError: If validation fails (from Domain)
            ValueError: If address validation fails (from Address VO)
        """
        # 1. Fetch restaurant
        restaurant = await self._restaurant_repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise RestaurantNotFoundError(str(restaurant_id))

        # 2. Create new Address if any address field is provided
        new_address = None
        if any([dto.street, dto.city, dto.postal_code]):
            new_address = Address(
                street=dto.street or restaurant.address.street,
                city=dto.city or restaurant.address.city,
                postal_code=dto.postal_code or restaurant.address.postal_code,
                latitude=(
                    dto.latitude if dto.latitude is not None else restaurant.address.latitude
                ),
                longitude=(
                    dto.longitude if dto.longitude is not None else restaurant.address.longitude
                ),
            )

        # 3. Update restaurant entity (validates business rules)
        restaurant.update_info(
            name=dto.name,
            description=dto.description,
            address=new_address,
            cuisine=dto.cuisine,
        )

        # 4. Save to repository
        updated_restaurant = await self._restaurant_repository.update(restaurant)

        # 5. Return DTO
        return RestaurantResponseDTO.from_entity(updated_restaurant)
