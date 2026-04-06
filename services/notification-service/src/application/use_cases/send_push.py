"""Send push notification use case."""

import structlog

from src.application.dto.notification import NotificationResponseDTO, SendPushDTO
from src.application.interfaces.channel_clients import IPushClient
from src.application.interfaces.event_publisher import INotificationEventPublisher
from src.application.interfaces.notification_repository import INotificationRepository
from src.application.interfaces.template_renderer import ITemplateRenderer
from src.domain.entities.notification import Notification
from src.domain.value_objects.notification_type import NotificationType

logger = structlog.get_logger(__name__)


class SendPushUseCase:
    """Send push notification using templates."""

    def __init__(
        self,
        repository: INotificationRepository,
        template_renderer: ITemplateRenderer,
        push_client: IPushClient,
        event_publisher: INotificationEventPublisher,
    ) -> None:
        self._repository = repository
        self._template_renderer = template_renderer
        self._push_client = push_client
        self._event_publisher = event_publisher

    async def execute(self, dto: SendPushDTO) -> NotificationResponseDTO:
        """Render, send, and persist push notification."""
        rendered = self._template_renderer.render(dto.template_name, dto.template_context)
        notification = Notification.create(
            notification_type=NotificationType.PUSH,
            recipient=dto.recipient,
            template_name=dto.template_name,
            subject=rendered.subject,
            body=rendered.body,
            aggregate_id=dto.aggregate_id,
            event_type=dto.event_type,
            user_id=dto.user_id,
        )
        provider_message_id = await self._push_client.send(
            recipient=notification.recipient,
            title=notification.subject,
            body=notification.body,
        )
        notification.mark_sent(provider_message_id)
        saved = await self._repository.save(notification)

        try:
            await self._event_publisher.publish_push_sent(saved)
        except Exception:
            logger.exception(
                "notification.push_event_publish_failed",
                notification_id=str(saved.id),
                aggregate_id=saved.aggregate_id,
            )

        return NotificationResponseDTO.from_entity(saved)
