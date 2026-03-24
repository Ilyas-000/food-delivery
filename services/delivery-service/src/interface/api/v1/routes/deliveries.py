"""Delivery API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.application.dto.delivery import AssignCourierDTO
from src.application.use_cases.assign_courier import AssignCourierUseCase
from src.application.use_cases.cancel_assignment import CancelAssignmentUseCase
from src.interface.api.v1.schemas.delivery import (
    AssignCourierRequest,
    DeliveryAssignmentResponse,
)
from src.interface.dependencies.delivery import (
    get_assign_courier_use_case,
    get_cancel_assignment_use_case,
)

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
