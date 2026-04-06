"""Review dependency providers."""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.review_repository import IReviewRepository
from src.application.interfaces.validation_clients import (
    IDeliveryValidationClient,
    IOrderValidationClient,
)
from src.application.use_cases.create_review import CreateReviewUseCase
from src.application.use_cases.delete_review import DeleteReviewUseCase
from src.application.use_cases.get_courier_rating import GetCourierRatingUseCase
from src.application.use_cases.get_restaurant_rating import GetRestaurantRatingUseCase
from src.application.use_cases.get_review import GetReviewUseCase
from src.application.use_cases.list_reviews import ListReviewsUseCase
from src.application.use_cases.update_review import UpdateReviewUseCase
from src.config import settings
from src.infrastructure.clients.review_validation_clients import (
    DeliveryValidationHttpClient,
    OrderValidationHttpClient,
)
from src.interface.dependencies.database import get_review_repository


async def get_order_validation_client() -> IOrderValidationClient:
    """Provide order-service validation client."""
    return OrderValidationHttpClient(
        base_url=settings.order_service_url,
        timeout_seconds=settings.upstream_timeout_seconds,
    )


async def get_delivery_validation_client() -> IDeliveryValidationClient:
    """Provide delivery-service validation client."""
    return DeliveryValidationHttpClient(
        base_url=settings.delivery_service_url,
        timeout_seconds=settings.upstream_timeout_seconds,
    )


async def get_create_review_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
    order_client: Annotated[IOrderValidationClient, Depends(get_order_validation_client)],
    delivery_client: Annotated[IDeliveryValidationClient, Depends(get_delivery_validation_client)],
) -> CreateReviewUseCase:
    """Provide create review use case."""
    return CreateReviewUseCase(repository, order_client, delivery_client)


async def get_get_review_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
) -> GetReviewUseCase:
    """Provide get review use case."""
    return GetReviewUseCase(repository)


async def get_list_reviews_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
) -> ListReviewsUseCase:
    """Provide list reviews use case."""
    return ListReviewsUseCase(repository)


async def get_update_review_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
) -> UpdateReviewUseCase:
    """Provide update review use case."""
    return UpdateReviewUseCase(repository)


async def get_delete_review_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
) -> DeleteReviewUseCase:
    """Provide delete review use case."""
    return DeleteReviewUseCase(repository)


async def get_restaurant_rating_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
) -> GetRestaurantRatingUseCase:
    """Provide rating summary use case."""
    return GetRestaurantRatingUseCase(repository)


async def get_courier_rating_use_case(
    repository: Annotated[IReviewRepository, Depends(get_review_repository)],
) -> GetCourierRatingUseCase:
    """Provide courier rating summary use case."""
    return GetCourierRatingUseCase(repository)
