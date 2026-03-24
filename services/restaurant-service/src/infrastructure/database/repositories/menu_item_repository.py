"""SQLAlchemy repository for menu item persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.domain.entities.menu_item import MenuItem
from src.domain.value_objects.category import Category
from src.domain.value_objects.price import Price
from src.infrastructure.database.models.menu_item_model import MenuItemModel

logger = structlog.get_logger(__name__)


class MenuItemRepository(IMenuItemRepository):
    """Persist and query `MenuItem` entities via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session (injected)
        """
        self._session = session

    async def create(self, menu_item: MenuItem) -> MenuItem:
        """
        Create new menu item in database.

        Flow:
        1. Convert Entity → Model
        2. Add to session
        3. Commit transaction
        4. Convert Model → Entity
        5. Return Entity

        Args:
            menu_item: MenuItem domain entity

        Returns:
            MenuItem: Created menu item entity

        Raises:
            Exception: If database error occurs
        """
        logger.info("repository.create_menu_item.started", menu_item_id=str(menu_item.id))

        # Entity → Model mapping
        menu_item_model = self._entity_to_model(menu_item)

        try:
            # Add to session and commit
            self._session.add(menu_item_model)
            await self._session.commit()
            await self._session.refresh(menu_item_model)  # Get DB-generated fields

            logger.info("repository.create_menu_item.success", menu_item_id=str(menu_item.id))

            # Model → Entity mapping
            return self._model_to_entity(menu_item_model)

        except IntegrityError as e:
            # Database constraint violation
            await self._session.rollback()
            logger.exception(
                "repository.create_menu_item.integrity_error",
                menu_item_id=str(menu_item.id),
                error=str(e),
            )
            raise

        except Exception as e:
            # Other database errors
            await self._session.rollback()
            logger.exception(
                "repository.create_menu_item.error",
                menu_item_id=str(menu_item.id),
                error=str(e),
            )
            raise

    async def get_by_id(self, menu_item_id: UUID) -> MenuItem | None:
        """
        Get menu item by ID.

        Uses SQLAlchemy 2.0 async select() style.

        Args:
            menu_item_id: MenuItem UUID

        Returns:
            MenuItem | None: MenuItem entity or None if not found
        """
        logger.debug("repository.get_menu_item_by_id", menu_item_id=str(menu_item_id))

        # SQLAlchemy 2.0 style query
        stmt = select(MenuItemModel).where(MenuItemModel.id == menu_item_id)
        result = await self._session.execute(stmt)
        menu_item_model = result.scalar_one_or_none()

        if menu_item_model is None:
            logger.debug("repository.get_menu_item_by_id.not_found", menu_item_id=str(menu_item_id))
            return None

        # Model → Entity
        return self._model_to_entity(menu_item_model)

    async def get_by_restaurant_id(
        self,
        restaurant_id: UUID,
        category: Category | None = None,
    ) -> list[MenuItem]:
        """
        Get all menu items for a restaurant.

        Uses indexed restaurant_id for efficient querying.

        Args:
            restaurant_id: Restaurant UUID
            category: Optional category filter

        Returns:
            list[MenuItem]: List of menu item entities
        """
        logger.debug("repository.get_menu_items_by_restaurant", restaurant_id=str(restaurant_id))

        stmt = select(MenuItemModel).where(MenuItemModel.restaurant_id == restaurant_id)
        if category is not None:
            stmt = stmt.where(MenuItemModel.category == category)
        result = await self._session.execute(stmt)
        menu_item_models = result.scalars().all()

        logger.debug(
            "repository.get_menu_items_by_restaurant.result",
            restaurant_id=str(restaurant_id),
            count=len(menu_item_models),
        )

        return [self._model_to_entity(model) for model in menu_item_models]

    async def update(self, menu_item: MenuItem) -> MenuItem:
        """
        Update existing menu item.

        Explicitly checks if menu item exists before updating.

        Args:
            menu_item: MenuItem entity with updated fields

        Returns:
            MenuItem: Updated menu item entity

        Raises:
            ValueError: If menu item not found
            Exception: If update fails
        """
        logger.info("repository.update_menu_item.started", menu_item_id=str(menu_item.id))

        # Load existing menu item from DB
        existing_model = await self._session.get(MenuItemModel, menu_item.id)

        if existing_model is None:
            logger.warning("repository.update_menu_item.not_found", menu_item_id=str(menu_item.id))
            raise ValueError(f"MenuItem with id {menu_item.id} not found")

        try:
            # Update fields from entity
            existing_model.restaurant_id = menu_item.restaurant_id
            existing_model.name = menu_item.name
            existing_model.description = menu_item.description
            existing_model.price_amount = menu_item.price.amount
            existing_model.price_currency = menu_item.price.currency
            existing_model.category = menu_item.category
            existing_model.image_url = menu_item.image_url
            existing_model.availability = menu_item.availability
            existing_model.updated_at = menu_item.updated_at

            # Commit changes
            await self._session.commit()
            await self._session.refresh(existing_model)

            logger.info("repository.update_menu_item.success", menu_item_id=str(menu_item.id))

            return self._model_to_entity(existing_model)

        except Exception as e:
            await self._session.rollback()
            logger.exception(
                "repository.update_menu_item.error",
                menu_item_id=str(menu_item.id),
                error=str(e),
            )
            raise

    async def delete(self, menu_item_id: UUID) -> None:
        """
        Delete menu item (hard delete).

        Note: Recommended to use discontinue() for soft delete.

        Args:
            menu_item_id: MenuItem UUID

        Raises:
            ValueError: If menu item not found
            Exception: If delete fails
        """
        logger.info("repository.delete_menu_item.started", menu_item_id=str(menu_item_id))

        menu_item_model = await self._session.get(MenuItemModel, menu_item_id)

        if menu_item_model is None:
            logger.warning("repository.delete_menu_item.not_found", menu_item_id=str(menu_item_id))
            raise ValueError(f"MenuItem with id {menu_item_id} not found")

        try:
            await self._session.delete(menu_item_model)
            await self._session.commit()

            logger.info("repository.delete_menu_item.success", menu_item_id=str(menu_item_id))

        except Exception as e:
            await self._session.rollback()
            logger.exception(
                "repository.delete_menu_item.error",
                menu_item_id=str(menu_item_id),
                error=str(e),
            )
            raise

    # Private mapping methods

    def _entity_to_model(self, menu_item: MenuItem) -> MenuItemModel:
        """
        Convert Domain Entity to ORM Model.

        Args:
            menu_item: Domain entity

        Returns:
            MenuItemModel: ORM model
        """
        return MenuItemModel(
            id=menu_item.id,
            restaurant_id=menu_item.restaurant_id,
            name=menu_item.name,
            description=menu_item.description,
            price_amount=menu_item.price.amount,
            price_currency=menu_item.price.currency,
            category=menu_item.category,
            image_url=menu_item.image_url,
            availability=menu_item.availability,
            created_at=menu_item.created_at,
            updated_at=menu_item.updated_at,
        )

    def _model_to_entity(self, model: MenuItemModel) -> MenuItem:
        """
        Convert ORM Model to Domain Entity.

        Args:
            model: ORM model

        Returns:
            MenuItem: Domain entity
        """
        price = Price(
            amount=model.price_amount,
            currency=model.price_currency,
        )

        return MenuItem(
            id=model.id,
            restaurant_id=model.restaurant_id,
            name=model.name,
            description=model.description,
            price=price,
            category=model.category,
            image_url=model.image_url,
            availability=model.availability,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
