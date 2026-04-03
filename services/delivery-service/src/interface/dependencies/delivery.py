"""Delivery dependency providers."""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.application.use_cases.assign_courier import AssignCourierUseCase
from src.application.use_cases.cancel_assignment import CancelAssignmentUseCase
from src.application.use_cases.complete_delivery import CompleteDeliveryUseCase
from src.application.use_cases.update_delivery_location import UpdateDeliveryLocationUseCase
from src.config import settings
from src.infrastructure.repositories.in_memory_assignment_repository import (
    InMemoryAssignmentRepository,
)
from src.interface.realtime.order_tracking_broadcaster import OrderTrackingBroadcaster

_REPOSITORY = InMemoryAssignmentRepository()
_ORDER_TRACKING_BROADCASTER = OrderTrackingBroadcaster(
    realtime_backend=settings.realtime_backend,
    redis_host=settings.redis_host,
    redis_port=settings.redis_port,
    redis_db=settings.redis_db,
    redis_password=settings.redis_password,
    redis_channel_prefix=settings.redis_channel_prefix,
)


async def get_assignment_repository() -> IAssignmentRepository:
    """Provide assignment repository implementation."""
    return _REPOSITORY


async def get_assign_courier_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> AssignCourierUseCase:
    """Provide assign courier use case."""
    return AssignCourierUseCase(repository=repository)


async def get_cancel_assignment_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> CancelAssignmentUseCase:
    """Provide cancel assignment use case."""
    return CancelAssignmentUseCase(repository=repository)


async def get_update_delivery_location_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> UpdateDeliveryLocationUseCase:
    """Provide update delivery location use case."""
    return UpdateDeliveryLocationUseCase(repository=repository)


async def get_complete_delivery_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> CompleteDeliveryUseCase:
    """Provide complete delivery use case."""
    return CompleteDeliveryUseCase(repository=repository)


async def get_order_tracking_broadcaster() -> OrderTrackingBroadcaster:
    """Provide shared broadcaster for order tracking."""
    return _ORDER_TRACKING_BROADCASTER


def get_order_tracking_broadcaster_instance() -> OrderTrackingBroadcaster:
    """Expose singleton broadcaster for application lifespan hooks."""
    return _ORDER_TRACKING_BROADCASTER
