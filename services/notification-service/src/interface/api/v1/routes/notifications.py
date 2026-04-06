"""Notification API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.application.dto.notification import SendEmailDTO, SendPushDTO
from src.application.use_cases.get_notification import GetNotificationUseCase
from src.application.use_cases.list_notifications import ListNotificationsUseCase
from src.application.use_cases.send_email import SendEmailUseCase
from src.application.use_cases.send_push import SendPushUseCase
from src.interface.api.v1.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    SendEmailRequest,
    SendPushRequest,
)
from src.interface.dependencies.notification import (
    get_get_notification_use_case,
    get_list_notifications_use_case,
    get_send_email_use_case,
    get_send_push_use_case,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/email", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_email_notification(
    request: SendEmailRequest,
    use_case: Annotated[SendEmailUseCase, Depends(get_send_email_use_case)],
) -> NotificationResponse:
    """Send email notification manually."""
    result = await use_case.execute(
        SendEmailDTO(
            recipient=request.recipient,
            template_name=request.template_name,
            template_context=request.template_context,
            aggregate_id=request.aggregate_id,
            event_type=request.event_type,
            user_id=request.user_id,
        )
    )
    return NotificationResponse.from_dto(result)


@router.post("/push", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_push_notification(
    request: SendPushRequest,
    use_case: Annotated[SendPushUseCase, Depends(get_send_push_use_case)],
) -> NotificationResponse:
    """Send push notification manually."""
    result = await use_case.execute(
        SendPushDTO(
            recipient=request.recipient,
            template_name=request.template_name,
            template_context=request.template_context,
            aggregate_id=request.aggregate_id,
            event_type=request.event_type,
            user_id=request.user_id,
        )
    )
    return NotificationResponse.from_dto(result)


@router.get("", response_model=NotificationListResponse, status_code=status.HTTP_200_OK)
async def list_notifications(
    use_case: Annotated[ListNotificationsUseCase, Depends(get_list_notifications_use_case)],
) -> NotificationListResponse:
    """Return notification history."""
    result = await use_case.execute()
    return NotificationListResponse.from_dto(result)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_notification(
    notification_id: UUID,
    use_case: Annotated[GetNotificationUseCase, Depends(get_get_notification_use_case)],
) -> NotificationResponse:
    """Return single notification."""
    result = await use_case.execute(notification_id)
    return NotificationResponse.from_dto(result)
