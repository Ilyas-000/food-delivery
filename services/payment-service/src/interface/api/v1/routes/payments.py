"""Payment API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.application.dto.payment import ReservePaymentDTO
from src.application.use_cases.release_payment import ReleasePaymentUseCase
from src.application.use_cases.reserve_payment import ReservePaymentUseCase
from src.interface.api.v1.schemas.payment import (
    PaymentReservationResponse,
    ReservePaymentRequest,
)
from src.interface.dependencies.payment import (
    get_release_payment_use_case,
    get_reserve_payment_use_case,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/reservations",
    response_model=PaymentReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reserve_payment(
    request: ReservePaymentRequest,
    use_case: Annotated[ReservePaymentUseCase, Depends(get_reserve_payment_use_case)],
) -> PaymentReservationResponse:
    """Reserve payment for order."""
    dto = ReservePaymentDTO(
        order_id=request.order_id,
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
    )
    result = await use_case.execute(dto)
    return PaymentReservationResponse.from_dto(result)


@router.delete(
    "/reservations/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def release_payment(
    reservation_id: UUID,
    use_case: Annotated[ReleasePaymentUseCase, Depends(get_release_payment_use_case)],
) -> Response:
    """Release payment reservation."""
    await use_case.execute(reservation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
