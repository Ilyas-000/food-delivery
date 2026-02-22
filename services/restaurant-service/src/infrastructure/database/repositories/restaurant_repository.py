"""
RestaurantRepository - SQLAlchemy implementation of IRestaurantRepository.

Repository Pattern implementation:

Repository Pattern:
- Abstracts data access
- Maps between Domain Entities and ORM Models
- Encapsulates queries and database logic
- Easy to test (can create mock/in-memory implementation)

Key responsibilities:
1. CRUD operations
2. Entity ↔ Model mapping
3. Database error handling
4. Query optimization
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.domain.entities.restaurant import Restaurant
from src.domain.exceptions.restaurant import RestaurantAlreadyExistsError
from src.domain.value_objects.address import Address
from src.domain.value_objects.cuisine import Cuisine
from src.infrastructure.database.models.restaurant_model import RestaurantModel

logger = structlog.get_logger(__name__)


class RestaurantRepository(IRestaurantRepository):
    """
    SQLAlchemy implementation of IRestaurantRepository.

    Implements Repository Pattern for working with restaurants.

    Architecture:
    - Accepts Domain Entity (Restaurant)
    - Converts to ORM Model (RestaurantModel)
    - Saves to PostgreSQL
    - On load converts back Model → Entity

    Dependencies:
    - session: AsyncSession (SQLAlchemy async session)

    Note: Repository does NOT know where session came from (DI)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session (injected)
        """
        self._session = session

    async def create(self, restaurant: Restaurant) -> Restaurant:
        """
        Create new restaurant in database.

        Flow:
        1. Convert Entity → Model
        2. Add to session
        3. Commit transaction
        4. Convert Model → Entity
        5. Return Entity

        Args:
            restaurant: Restaurant domain entity

        Returns:
            Restaurant: Created restaurant entity

        Raises:
            RestaurantAlreadyExistsError: If duplicate restaurant for owner
            Exception: If database error occurs
        """
        logger.info("repository.create_restaurant.started", restaurant_id=str(restaurant.id))

        # Entity → Model mapping
        restaurant_model = self._entity_to_model(restaurant)

        try:
            # Add to session and commit
            self._session.add(restaurant_model)
            await self._session.commit()
            await self._session.refresh(restaurant_model)  # Get DB-generated fields

            logger.info("repository.create_restaurant.success", restaurant_id=str(restaurant.id))

            # Model → Entity mapping
            return self._model_to_entity(restaurant_model)

        except IntegrityError as e:
            # Unique constraint violation
            await self._session.rollback()
            logger.exception(
                "repository.create_restaurant.integrity_error",
                restaurant_id=str(restaurant.id),
                error=str(e),
            )
            raise RestaurantAlreadyExistsError(restaurant.name, str(restaurant.owner_id)) from e

        except Exception as e:
            # Other database errors
            await self._session.rollback()
            logger.exception(
                "repository.create_restaurant.error",
                restaurant_id=str(restaurant.id),
                error=str(e),
            )
            raise

    async def get_by_id(self, restaurant_id: UUID) -> Restaurant | None:
        """
        Get restaurant by ID.

        Uses SQLAlchemy 2.0 async select() style.

        Args:
            restaurant_id: Restaurant UUID

        Returns:
            Restaurant | None: Restaurant entity or None if not found
        """
        logger.debug("repository.get_restaurant_by_id", restaurant_id=str(restaurant_id))

        # SQLAlchemy 2.0 style query
        stmt = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
        result = await self._session.execute(stmt)
        restaurant_model = result.scalar_one_or_none()

        if restaurant_model is None:
            logger.debug(
                "repository.get_restaurant_by_id.not_found", restaurant_id=str(restaurant_id)
            )
            return None

        # Model → Entity
        return self._model_to_entity(restaurant_model)

    async def get_by_owner_and_name(self, owner_id: UUID, name: str) -> Restaurant | None:
        """
        Get restaurant by owner and name.

        Used for duplicate checking during creation.

        Args:
            owner_id: Owner UUID
            name: Restaurant name

        Returns:
            Restaurant | None: Restaurant entity or None if not found
        """
        logger.debug(
            "repository.get_restaurant_by_owner_and_name", owner_id=str(owner_id), name=name
        )

        stmt = select(RestaurantModel).where(
            RestaurantModel.owner_id == owner_id, RestaurantModel.name == name
        )
        result = await self._session.execute(stmt)
        restaurant_model = result.scalar_one_or_none()

        if restaurant_model is None:
            return None

        return self._model_to_entity(restaurant_model)

    async def get_by_owner_id(self, owner_id: UUID) -> list[Restaurant]:
        """
        Get all restaurants by owner ID.

        Args:
            owner_id: Owner UUID

        Returns:
            list[Restaurant]: List of restaurant entities
        """
        logger.debug("repository.get_restaurants_by_owner", owner_id=str(owner_id))

        stmt = select(RestaurantModel).where(RestaurantModel.owner_id == owner_id)
        result = await self._session.execute(stmt)
        restaurant_models = result.scalars().all()

        return [self._model_to_entity(model) for model in restaurant_models]

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

        Uses indexed columns for efficient filtering.

        Args:
            cuisine: Filter by cuisine type
            city: Filter by city
            min_rating: Minimum rating filter
            is_active: Filter active/inactive restaurants
            limit: Maximum results to return
            offset: Results offset for pagination

        Returns:
            list[Restaurant]: List of matching restaurants
        """
        logger.debug(
            "repository.search_restaurants",
            cuisine=cuisine,
            city=city,
            min_rating=min_rating,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        # Build query with filters
        stmt = select(RestaurantModel)

        if cuisine is not None:
            stmt = stmt.where(RestaurantModel.cuisine == cuisine)

        if city is not None:
            stmt = stmt.where(RestaurantModel.city == city)

        if min_rating is not None:
            stmt = stmt.where(RestaurantModel.rating >= Decimal(str(min_rating)))

        stmt = stmt.where(RestaurantModel.is_active == is_active)

        # Order by rating desc (best first)
        stmt = stmt.order_by(RestaurantModel.rating.desc())

        # Pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self._session.execute(stmt)
        restaurant_models = result.scalars().all()

        logger.debug(
            "repository.search_restaurants.result",
            count=len(restaurant_models),
        )

        return [self._model_to_entity(model) for model in restaurant_models]

    async def update(self, restaurant: Restaurant) -> Restaurant:
        """
        Update existing restaurant.

        Explicitly checks if restaurant exists before updating.

        Args:
            restaurant: Restaurant entity with updated fields

        Returns:
            Restaurant: Updated restaurant entity

        Raises:
            ValueError: If restaurant not found
            Exception: If update fails
        """
        logger.info("repository.update_restaurant.started", restaurant_id=str(restaurant.id))

        # Load existing restaurant from DB
        existing_model = await self._session.get(RestaurantModel, restaurant.id)

        if existing_model is None:
            logger.warning(
                "repository.update_restaurant.not_found", restaurant_id=str(restaurant.id)
            )
            raise ValueError(f"Restaurant with id {restaurant.id} not found")

        try:
            # Update fields from entity
            existing_model.owner_id = restaurant.owner_id
            existing_model.name = restaurant.name
            existing_model.description = restaurant.description
            existing_model.street = restaurant.address.street
            existing_model.city = restaurant.address.city
            existing_model.postal_code = restaurant.address.postal_code
            existing_model.latitude = restaurant.address.latitude
            existing_model.longitude = restaurant.address.longitude
            existing_model.cuisine = restaurant.cuisine
            existing_model.rating = restaurant.rating
            existing_model.is_active = restaurant.is_active
            existing_model.updated_at = restaurant.updated_at

            # Commit changes
            await self._session.commit()
            await self._session.refresh(existing_model)

            logger.info("repository.update_restaurant.success", restaurant_id=str(restaurant.id))

            return self._model_to_entity(existing_model)

        except Exception as e:
            await self._session.rollback()
            logger.exception(
                "repository.update_restaurant.error",
                restaurant_id=str(restaurant.id),
                error=str(e),
            )
            raise

    async def delete(self, restaurant_id: UUID) -> None:
        """
        Delete restaurant (soft delete, sets is_active=False).

        Args:
            restaurant_id: Restaurant UUID

        Raises:
            ValueError: If restaurant not found
            Exception: If delete fails
        """
        logger.info("repository.delete_restaurant.started", restaurant_id=str(restaurant_id))

        restaurant_model = await self._session.get(RestaurantModel, restaurant_id)

        if restaurant_model is None:
            logger.warning(
                "repository.delete_restaurant.not_found", restaurant_id=str(restaurant_id)
            )
            raise ValueError(f"Restaurant with id {restaurant_id} not found")

        try:
            restaurant_model.is_active = False
            restaurant_model.updated_at = datetime.now(UTC)
            await self._session.commit()

            logger.info("repository.delete_restaurant.success", restaurant_id=str(restaurant_id))

        except Exception as e:
            await self._session.rollback()
            logger.exception(
                "repository.delete_restaurant.error",
                restaurant_id=str(restaurant_id),
                error=str(e),
            )
            raise

    # Private mapping methods

    def _entity_to_model(self, restaurant: Restaurant) -> RestaurantModel:
        """
        Convert Domain Entity to ORM Model.

        Args:
            restaurant: Domain entity

        Returns:
            RestaurantModel: ORM model
        """
        return RestaurantModel(
            id=restaurant.id,
            owner_id=restaurant.owner_id,
            name=restaurant.name,
            description=restaurant.description,
            street=restaurant.address.street,
            city=restaurant.address.city,
            postal_code=restaurant.address.postal_code,
            latitude=restaurant.address.latitude,
            longitude=restaurant.address.longitude,
            cuisine=restaurant.cuisine,
            rating=restaurant.rating,
            is_active=restaurant.is_active,
            created_at=restaurant.created_at,
            updated_at=restaurant.updated_at,
        )

    def _model_to_entity(self, model: RestaurantModel) -> Restaurant:
        """
        Convert ORM Model to Domain Entity.

        Args:
            model: ORM model

        Returns:
            Restaurant: Domain entity
        """
        address = Address(
            street=model.street,
            city=model.city,
            postal_code=model.postal_code,
            latitude=float(model.latitude) if model.latitude is not None else None,
            longitude=float(model.longitude) if model.longitude is not None else None,
        )

        return Restaurant(
            id=model.id,
            owner_id=model.owner_id,
            name=model.name,
            description=model.description,
            address=address,
            cuisine=model.cuisine,
            rating=model.rating,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
