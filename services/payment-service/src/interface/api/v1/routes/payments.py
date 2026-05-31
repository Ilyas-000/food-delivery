"""Payment API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response, status

from src.application.dto.payment import ReservePaymentDTO
from src.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from src.application.use_cases.get_payment import GetPaymentUseCase
from src.application.use_cases.get_payment_history import GetPaymentHistoryUseCase
from src.application.use_cases.refund_payment import RefundPaymentUseCase
from src.application.use_cases.release_payment import ReleasePaymentUseCase
from src.application.use_cases.reserve_payment import ReservePaymentUseCase
from src.interface.api.v1.schemas.payment import (
    PaymentHistoryResponse,
    PaymentReservationResponse,
    PaymentResponse,
    ReservePaymentRequest,
)
from src.interface.dependencies.payment import (
    get_confirm_payment_use_case,
    get_payment_history_use_case,
    get_payment_use_case,
    get_refund_payment_use_case,
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
    http_request: Request,
    request: ReservePaymentRequest,
    use_case: Annotated[ReservePaymentUseCase, Depends(get_reserve_payment_use_case)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PaymentReservationResponse:
    """Reserve payment for order."""
    cleaned_idempotency_key = None
    if idempotency_key is not None and idempotency_key.strip():
        cleaned_idempotency_key = idempotency_key.strip()

    dto = ReservePaymentDTO(
        order_id=request.order_id,
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        idempotency_key=cleaned_idempotency_key,
    )
    result = await use_case.execute(dto)
    http_request.app.state.payment_reservations_total.labels(result="success").inc()
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


@router.get(
    "/history",
    response_model=PaymentHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment_history(
    use_case: Annotated[GetPaymentHistoryUseCase, Depends(get_payment_history_use_case)],
    order_id: UUID | None = None,
    user_id: UUID | None = None,
) -> PaymentHistoryResponse:
    """Get payment history with optional filters."""
    result = await use_case.execute(order_id=order_id, user_id=user_id)
    return PaymentHistoryResponse.from_dto(result)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment(
    payment_id: UUID,
    use_case: Annotated[GetPaymentUseCase, Depends(get_payment_use_case)],
) -> PaymentResponse:
    """Get payment by id."""
    result = await use_case.execute(payment_id)
    return PaymentResponse.from_dto(result)


@router.post(
    "/{payment_id}/confirm",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_payment(
    request: Request,
    payment_id: UUID,
    use_case: Annotated[ConfirmPaymentUseCase, Depends(get_confirm_payment_use_case)],
) -> PaymentResponse:
    """Confirm reserved payment."""
    result = await use_case.execute(payment_id)
    request.app.state.payment_confirmations_total.labels(result="success").inc()
    return PaymentResponse.from_dto(result)


@router.post(
    "/{payment_id}/refund",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
async def refund_payment(
    request: Request,
    payment_id: UUID,
    use_case: Annotated[RefundPaymentUseCase, Depends(get_refund_payment_use_case)],
) -> PaymentResponse:
    """Refund completed payment."""
    result = await use_case.execute(payment_id)
    request.app.state.payment_refunds_total.labels(result="success").inc()
    return PaymentResponse.from_dto(result)
