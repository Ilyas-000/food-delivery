"""
CreateRestaurant Use Case.

Creates a new restaurant.
"""

from src.application.dto import CreateRestaurantDTO, RestaurantResponseDTO
from src.application.interfaces import IRestaurantRepository
from src.domain.entities import Restaurant
from src.domain.exceptions import RestaurantAlreadyExistsError
from src.domain.value_objects import Address


class CreateRestaurantUseCase:
    """
    Use case for creating a new restaurant.

    Business flow:
    1. Check if restaurant with same name already exists for owner
    2. Create Address value object
    3. Create Restaurant entity (validates business rules)
    4. Save to repository
    5. Return DTO

    This is where orchestration happens - no business logic here!
    Business logic is in Domain layer (Restaurant.create, Address validation).
    """

    def __init__(self, restaurant_repository: IRestaurantRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            restaurant_repository: Restaurant repository interface
        """
        self._restaurant_repository = restaurant_repository

    async def execute(self, dto: CreateRestaurantDTO) -> RestaurantResponseDTO:
        """
        Execute use case.

        Args:
            dto: Create restaurant data

        Returns:
            RestaurantResponseDTO: Created restaurant

        Raises:
            RestaurantAlreadyExistsError: If restaurant with same name exists for owner
            InvalidRestaurantDataError: If validation fails (from Domain)
            ValueError: If address validation fails (from Address VO)
        """
        # 1. Check for duplicates
        existing = await self._restaurant_repository.get_by_owner_and_name(dto.owner_id, dto.name)
        if existing is not None:
            raise RestaurantAlreadyExistsError(dto.name, str(dto.owner_id))

        # 2. Create Address value object (validates address)
        address = Address(
            street=dto.street,
            city=dto.city,
            postal_code=dto.postal_code,
            latitude=dto.latitude,
            longitude=dto.longitude,
        )

        # 3. Create Restaurant entity (validates business rules)
        restaurant = Restaurant.create(
            owner_id=dto.owner_id,
            name=dto.name,
            description=dto.description,
            address=address,
            cuisine=dto.cuisine,
        )

        # 4. Save to repository
        created_restaurant = await self._restaurant_repository.create(restaurant)

        # 5. Return DTO
        return RestaurantResponseDTO.from_entity(created_restaurant)
