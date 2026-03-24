"""SQLAlchemy repository implementation for orders."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from src.application.interfaces.order_repository import IOrderRepository
from src.domain.entities.order import Order
from src.domain.exceptions.order import OrderNotFoundError
from src.domain.value_objects.order_item import OrderItem
from src.infrastructure.database.models.order_model import OrderItemModel, OrderModel

logger = structlog.get_logger(__name__)


class SqlAlchemyOrderRepository(IOrderRepository):
    """Persist and load orders through SQLAlchemy models."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, order: Order) -> Order:
        """Create order and related items."""
        model = self._entity_to_model(order)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        loaded = await self._load_model(order.id)
        return self._model_to_entity(loaded)

    async def get_by_id(self, order_id: UUID) -> Order | None:
        """Get order by id with line items."""
        stmt = (
            select(OrderModel)
            .where(OrderModel.id == order_id)
            .options(selectinload(OrderModel.items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def update(self, order: Order) -> Order:
        """Update order state and replace line items."""
        existing = await self._load_model(order.id, raise_if_missing=True)

        existing.user_id = order.user_id
        existing.restaurant_id = order.restaurant_id
        existing.status = order.status
        existing.total_amount = order.total_amount
        existing.cancellation_reason = order.cancellation_reason
        existing.created_at = order.created_at
        existing.updated_at = order.updated_at
        existing.items = [
            OrderItemModel(
                order_id=order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                currency=item.currency,
                position=idx,
            )
            for idx, item in enumerate(order.items)
        ]

        await self._session.commit()
        loaded = await self._load_model(order.id, raise_if_missing=True)
        return self._model_to_entity(loaded)

    async def _load_model(self, order_id: UUID, raise_if_missing: bool = False) -> OrderModel:
        """Load OrderModel with items by id."""
        stmt = (
            select(OrderModel)
            .where(OrderModel.id == order_id)
            .options(selectinload(OrderModel.items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            if raise_if_missing:
                raise OrderNotFoundError(f"order '{order_id}' not found")
            raise RuntimeError(f"order '{order_id}' not found")

        return model

    def _entity_to_model(self, order: Order) -> OrderModel:
        """Map Order entity to OrderModel."""
        model = OrderModel(
            id=order.id,
            user_id=order.user_id,
            restaurant_id=order.restaurant_id,
            status=order.status,
            total_amount=order.total_amount,
            cancellation_reason=order.cancellation_reason,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        model.items = [
            OrderItemModel(
                order_id=order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                currency=item.currency,
                position=idx,
            )
            for idx, item in enumerate(order.items)
        ]
        return model

    def _model_to_entity(self, model: OrderModel) -> Order:
        """Map OrderModel to Order entity."""
        sorted_items = sorted(model.items, key=lambda item: item.position)
        entity_items = tuple(
            OrderItem(
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                unit_price=Decimal(str(item.unit_price)),
                currency=item.currency,
            )
            for item in sorted_items
        )
        return Order(
            id=model.id,
            user_id=model.user_id,
            restaurant_id=model.restaurant_id,
            items=entity_items,
            total_amount=Decimal(str(model.total_amount)),
            status=model.status,
            cancellation_reason=model.cancellation_reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
