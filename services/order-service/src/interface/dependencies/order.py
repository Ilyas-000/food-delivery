"""Order dependencies for FastAPI endpoints."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.order_repository import IOrderRepository
from src.application.interfaces.saga_step import ISagaStep
from src.application.use_cases.create_order import CreateOrderUseCase
from src.application.use_cases.get_order import GetOrderUseCase
from src.config import settings
from src.infrastructure.clients.http_service_clients import (
    DeliveryServiceHttpClient,
    PaymentServiceHttpClient,
    RestaurantServiceHttpClient,
)
from src.infrastructure.database.repositories.sqlalchemy_order_repository import (
    SqlAlchemyOrderRepository,
)
from src.infrastructure.repositories.in_memory_order_repository import InMemoryOrderRepository
from src.infrastructure.saga.http_steps import (
    AssignCourierStep as HttpAssignCourierStep,
)
from src.infrastructure.saga.http_steps import (
    ReservePaymentStep as HttpReservePaymentStep,
)
from src.infrastructure.saga.http_steps import (
    ValidateMenuItemsStep as HttpValidateMenuItemsStep,
)
from src.infrastructure.saga.mock_steps import (
    AssignCourierStep as MockAssignCourierStep,
)
from src.infrastructure.saga.mock_steps import (
    ReservePaymentStep as MockReservePaymentStep,
)
from src.infrastructure.saga.mock_steps import (
    ValidateMenuItemsStep as MockValidateMenuItemsStep,
)
from src.interface.dependencies.database import get_optional_db_session

_ORDER_REPOSITORY = InMemoryOrderRepository()


async def get_order_repository(
    session: Annotated[AsyncSession | None, Depends(get_optional_db_session)],
) -> IOrderRepository:
    """Provide repository implementation based on configured backend."""
    if settings.repository_backend == "postgres":
        if session is None:
            raise RuntimeError("Database is not initialized")
        return SqlAlchemyOrderRepository(session)

    return _ORDER_REPOSITORY


def _build_saga_steps() -> tuple[ISagaStep, ...]:
    """Build saga steps sequence for order creation flow."""
    if settings.saga_backend == "http":
        restaurant_client = RestaurantServiceHttpClient(
            base_url=settings.restaurant_service_url,
            timeout_seconds=settings.saga_step_timeout_seconds,
        )
        payment_client = PaymentServiceHttpClient(
            base_url=settings.payment_service_url,
            timeout_seconds=settings.saga_step_timeout_seconds,
        )
        delivery_client = DeliveryServiceHttpClient(
            base_url=settings.delivery_service_url,
            timeout_seconds=settings.saga_step_timeout_seconds,
        )
        return (
            HttpValidateMenuItemsStep(restaurant_client=restaurant_client),
            HttpReservePaymentStep(payment_client=payment_client),
            HttpAssignCourierStep(delivery_client=delivery_client),
        )

    if settings.saga_backend != "mock":
        raise RuntimeError(
            f"Unsupported ORDER_SERVICE_SAGA_BACKEND='{settings.saga_backend}'. "
            "Use 'mock' or 'http'."
        )

    return (
        MockValidateMenuItemsStep(),
        MockReservePaymentStep(),
        MockAssignCourierStep(),
    )


async def get_create_order_use_case(
    repository: Annotated[IOrderRepository, Depends(get_order_repository)],
) -> CreateOrderUseCase:
    """Provide CreateOrderUseCase."""
    return CreateOrderUseCase(repository=repository, saga_steps=_build_saga_steps())


async def get_get_order_use_case(
    repository: Annotated[IOrderRepository, Depends(get_order_repository)],
) -> GetOrderUseCase:
    """Provide GetOrderUseCase."""
    return GetOrderUseCase(repository=repository)
