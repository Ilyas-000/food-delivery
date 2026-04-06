"""Delivery dependency providers."""

from typing import Annotated, cast

from fastapi import Depends

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.application.interfaces.courier_allocator import ICourierAllocator
from src.application.interfaces.event_publisher import IDeliveryEventPublisher
from src.application.use_cases.assign_courier import AssignCourierUseCase
from src.application.use_cases.cancel_assignment import CancelAssignmentUseCase
from src.application.use_cases.complete_delivery import CompleteDeliveryUseCase
from src.application.use_cases.get_assignment_by_order import GetAssignmentByOrderUseCase
from src.application.use_cases.update_delivery_location import UpdateDeliveryLocationUseCase
from src.config import settings
from src.infrastructure.events.publisher import KafkaDeliveryEventPublisher
from src.infrastructure.repositories.in_memory_assignment_repository import (
    InMemoryAssignmentRepository,
)
from src.infrastructure.repositories.round_robin_courier_allocator import (
    RoundRobinCourierAllocator,
)
from src.interface.realtime.order_tracking_broadcaster import OrderTrackingBroadcaster

_REPOSITORY = InMemoryAssignmentRepository()
_EVENT_PUBLISHER = KafkaDeliveryEventPublisher()
_COURIER_ALLOCATOR = RoundRobinCourierAllocator(settings.courier_ids)
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


async def get_delivery_event_publisher() -> IDeliveryEventPublisher:
    """Provide delivery event publisher."""
    return cast(IDeliveryEventPublisher, _EVENT_PUBLISHER)


async def get_courier_allocator() -> ICourierAllocator:
    """Provide shared courier allocator."""
    return _COURIER_ALLOCATOR


async def get_assign_courier_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
    event_publisher: Annotated[IDeliveryEventPublisher, Depends(get_delivery_event_publisher)],
    courier_allocator: Annotated[ICourierAllocator, Depends(get_courier_allocator)],
) -> AssignCourierUseCase:
    """Provide assign courier use case."""
    return AssignCourierUseCase(
        repository=repository,
        event_publisher=event_publisher,
        courier_allocator=courier_allocator,
    )


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


async def get_assignment_by_order_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> GetAssignmentByOrderUseCase:
    """Provide assignment lookup use case."""
    return GetAssignmentByOrderUseCase(repository=repository)


async def get_order_tracking_broadcaster() -> OrderTrackingBroadcaster:
    """Provide shared broadcaster for order tracking."""
    return _ORDER_TRACKING_BROADCASTER


def get_order_tracking_broadcaster_instance() -> OrderTrackingBroadcaster:
    """Expose singleton broadcaster for application lifespan hooks."""
    return _ORDER_TRACKING_BROADCASTER
