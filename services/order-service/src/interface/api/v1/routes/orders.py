"""Order API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.application.dto.order import CreateOrderDTO, CreateOrderItemDTO
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.get_order import GetOrderUseCase
from src.infrastructure.events.publisher import publish_event
from src.interface.api.v1.schemas.order import CreateOrderRequest, OrderResponse
from src.interface.dependencies.order import get_create_order_use_case, get_get_order_use_case

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    use_case: Annotated[CreateOrderUseCase, Depends(get_create_order_use_case)],
) -> OrderResponse:
    """Create order via saga orchestrator."""
    dto = CreateOrderDTO(
        user_id=request.user_id,
        restaurant_id=request.restaurant_id,
        items=[
            CreateOrderItemDTO(
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                currency=item.currency,
            )
            for item in request.items
        ],
    )

    result = await use_case.execute(dto)

    await publish_event(
        event_type="order-service.order.created",
        aggregate_type="order",
        aggregate_id=str(result.id),
        user_id=str(result.user_id),
        payload={
            "restaurant_id": str(result.restaurant_id),
            "total_amount": str(result.total_amount),
            "status": result.status.value,
        },
    )
    await publish_event(
        event_type="order-service.order.confirmed",
        aggregate_type="order",
        aggregate_id=str(result.id),
        user_id=str(result.user_id),
        payload={
            "restaurant_id": str(result.restaurant_id),
            "total_amount": str(result.total_amount),
            "status": result.status.value,
        },
    )
    return OrderResponse.from_dto(result)


@router.get("/{order_id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def get_order(
    order_id: UUID,
    use_case: Annotated[GetOrderUseCase, Depends(get_get_order_use_case)],
) -> OrderResponse:
    """Get order by id."""
    result = await use_case.execute(order_id)
    return OrderResponse.from_dto(result)
