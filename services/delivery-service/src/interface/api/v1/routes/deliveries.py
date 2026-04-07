"""Delivery API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.application.dto.delivery import AssignCourierDTO, UpdateDeliveryLocationDTO
from src.application.use_cases.assign_courier import AssignCourierUseCase
from src.application.use_cases.cancel_assignment import CancelAssignmentUseCase
from src.application.use_cases.complete_delivery import CompleteDeliveryUseCase
from src.application.use_cases.get_assignment_by_order import GetAssignmentByOrderUseCase
from src.application.use_cases.update_delivery_location import UpdateDeliveryLocationUseCase
from src.infrastructure.events.publisher import publish_event
from src.interface.api.v1.schemas.delivery import (
    AssignCourierRequest,
    DeliveryAssignmentResponse,
    UpdateDeliveryLocationRequest,
)
from src.interface.dependencies.delivery import (
    get_assign_courier_use_case,
    get_assignment_by_order_use_case,
    get_cancel_assignment_use_case,
    get_complete_delivery_use_case,
    get_order_tracking_broadcaster,
    get_update_delivery_location_use_case,
)
from src.interface.realtime.order_tracking_broadcaster import OrderTrackingBroadcaster

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.post(
    "/assignments",
    response_model=DeliveryAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_courier(
    request: AssignCourierRequest,
    use_case: Annotated[AssignCourierUseCase, Depends(get_assign_courier_use_case)],
) -> DeliveryAssignmentResponse:
    """Assign courier to order."""
    dto = AssignCourierDTO(
        order_id=request.order_id,
        restaurant_id=request.restaurant_id,
        courier_id=request.courier_id,
    )
    result = await use_case.execute(dto)
    return DeliveryAssignmentResponse.from_dto(result)


@router.delete(
    "/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_assignment(
    assignment_id: UUID,
    use_case: Annotated[CancelAssignmentUseCase, Depends(get_cancel_assignment_use_case)],
) -> Response:
    """Cancel delivery assignment."""
    await use_case.execute(assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/orders/{order_id}",
    response_model=DeliveryAssignmentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_assignment_by_order(
    order_id: UUID,
    use_case: Annotated[
        GetAssignmentByOrderUseCase,
        Depends(get_assignment_by_order_use_case),
    ],
) -> DeliveryAssignmentResponse:
    """Get delivery assignment by order id."""
    result = await use_case.execute(order_id)
    return DeliveryAssignmentResponse.from_dto(result)


@router.post(
    "/location",
    response_model=DeliveryAssignmentResponse,
    status_code=status.HTTP_200_OK,
)
async def update_location(
    request: UpdateDeliveryLocationRequest,
    use_case: Annotated[
        UpdateDeliveryLocationUseCase,
        Depends(get_update_delivery_location_use_case),
    ],
    broadcaster: Annotated[OrderTrackingBroadcaster, Depends(get_order_tracking_broadcaster)],
) -> DeliveryAssignmentResponse:
    """Update courier location and push real-time updates for order."""
    dto = UpdateDeliveryLocationDTO(
        order_id=request.order_id,
        latitude=request.latitude,
        longitude=request.longitude,
    )
    result = await use_case.execute(dto)
    await publish_event(
        event_type="delivery-service.delivery.location_updated",
        aggregate_type="delivery",
        aggregate_id=str(result.id),
        payload={
            "order_id": str(result.order_id),
            "status": result.status,
            "latitude": result.latitude,
            "longitude": result.longitude,
        },
    )

    await broadcaster.broadcast(
        order_id=result.order_id,
        event={
            "type": "location_update",
            "data": {
                "order_id": str(result.order_id),
                "assignment_id": str(result.id),
                "status": result.status,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "timestamp": result.updated_at.isoformat(),
            },
        },
    )
    return DeliveryAssignmentResponse.from_dto(result)


@router.post(
    "/{order_id}/complete",
    response_model=DeliveryAssignmentResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_delivery(
    order_id: UUID,
    use_case: Annotated[CompleteDeliveryUseCase, Depends(get_complete_delivery_use_case)],
    broadcaster: Annotated[OrderTrackingBroadcaster, Depends(get_order_tracking_broadcaster)],
) -> DeliveryAssignmentResponse:
    """Complete delivery for order."""
    result = await use_case.execute(order_id)
    await publish_event(
        event_type="delivery-service.delivery.completed",
        aggregate_type="delivery",
        aggregate_id=str(result.id),
        payload={
            "order_id": str(result.order_id),
            "status": result.status,
            "delivered_at": result.delivered_at.isoformat() if result.delivered_at else None,
        },
    )

    await broadcaster.broadcast(
        order_id=result.order_id,
        event={
            "type": "delivery_completed",
            "data": {
                "order_id": str(result.order_id),
                "assignment_id": str(result.id),
                "status": result.status,
                "delivered_at": result.delivered_at.isoformat() if result.delivered_at else None,
                "timestamp": result.updated_at.isoformat(),
            },
        },
    )
    return DeliveryAssignmentResponse.from_dto(result)
