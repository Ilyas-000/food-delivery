"""
Restaurant Repository Interface.

Defines the contract for restaurant persistence operations.
Infrastructure layer implements this interface.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Restaurant
from src.domain.value_objects import Cuisine


class IRestaurantRepository(ABC):
    """
    Restaurant repository interface.

    This interface defines all persistence operations for restaurants.
    Infrastructure layer provides the actual implementation using SQLAlchemy.

    Design pattern: Dependency Inversion Principle
    - Application layer depends on this interface (abstraction)
    - Infrastructure layer implements this interface (concrete)
    """

    @abstractmethod
    async def create(self, restaurant: Restaurant) -> Restaurant:
        """
        Create a new restaurant.

        Args:
            restaurant: Restaurant entity to persist

        Returns:
            Restaurant: Created restaurant with DB-generated fields

        Raises:
            RestaurantAlreadyExistsError: If restaurant with same name exists for owner
        """
        ...

    @abstractmethod
    async def get_by_id(self, restaurant_id: UUID) -> Restaurant | None:
        """
        Get restaurant by ID.

        Args:
            restaurant_id: Restaurant ID

        Returns:
            Restaurant | None: Restaurant if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_by_owner_and_name(self, owner_id: UUID, name: str) -> Restaurant | None:
        """
        Get restaurant by owner ID and name.

        Used to check for duplicates (same owner cannot have two restaurants with same name).

        Args:
            owner_id: Owner user ID
            name: Restaurant name

        Returns:
            Restaurant | None: Restaurant if found, None otherwise
        """
        ...

    @abstractmethod
    async def update(self, restaurant: Restaurant) -> Restaurant:
        """
        Update existing restaurant.

        Args:
            restaurant: Restaurant entity with updated fields

        Returns:
            Restaurant: Updated restaurant

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, restaurant_id: UUID) -> None:
        """
        Delete restaurant (soft delete - sets is_active=False).

        Args:
            restaurant_id: Restaurant ID

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist
        """
        ...

    @abstractmethod
    async def search(
        self,
        cuisine: Cuisine | None = None,
        city: str | None = None,
        min_rating: float | None = None,
        is_active: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Restaurant]:
        """
        Search restaurants with filters.

        Args:
            cuisine: Filter by cuisine type
            city: Filter by city
            min_rating: Minimum rating (0.0-5.0)
            is_active: Filter by active status (default True)
            limit: Max results (pagination)
            offset: Skip results (pagination)

        Returns:
            list[Restaurant]: List of matching restaurants
        """
        ...

    @abstractmethod
    async def get_by_owner_id(self, owner_id: UUID) -> list[Restaurant]:
        """
        Get all restaurants owned by user.

        Args:
            owner_id: Owner user ID

        Returns:
            list[Restaurant]: List of restaurants
        """
        ...
