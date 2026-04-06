"""Notification dependency providers."""

from src.application.interfaces.channel_clients import IEmailClient, IPushClient
from src.application.interfaces.event_publisher import INotificationEventPublisher
from src.application.interfaces.notification_repository import INotificationRepository
from src.application.interfaces.template_renderer import ITemplateRenderer
from src.application.use_cases.get_notification import GetNotificationUseCase
from src.application.use_cases.list_notifications import ListNotificationsUseCase
from src.application.use_cases.send_email import SendEmailUseCase
from src.application.use_cases.send_push import SendPushUseCase
from src.config import settings
from src.infrastructure.clients.mock_email_client import MockEmailClient
from src.infrastructure.clients.mock_push_client import MockPushClient
from src.infrastructure.consumers.event_consumer import NotificationEventConsumer
from src.infrastructure.consumers.processor import NotificationEventProcessor
from src.infrastructure.events.publisher import KafkaNotificationEventPublisher
from src.infrastructure.repositories.in_memory_notification_repository import (
    InMemoryNotificationRepository,
)
from src.infrastructure.templates.in_memory_template_renderer import InMemoryTemplateRenderer

_REPOSITORY = InMemoryNotificationRepository()
_EMAIL_CLIENT = MockEmailClient()
_PUSH_CLIENT = MockPushClient()
_TEMPLATE_RENDERER = InMemoryTemplateRenderer()
_EVENT_PUBLISHER = KafkaNotificationEventPublisher()
_EMAIL_USE_CASE = SendEmailUseCase(
    repository=_REPOSITORY,
    template_renderer=_TEMPLATE_RENDERER,
    email_client=_EMAIL_CLIENT,
    event_publisher=_EVENT_PUBLISHER,
)
_PUSH_USE_CASE = SendPushUseCase(
    repository=_REPOSITORY,
    template_renderer=_TEMPLATE_RENDERER,
    push_client=_PUSH_CLIENT,
    event_publisher=_EVENT_PUBLISHER,
)
_EVENT_PROCESSOR = NotificationEventProcessor(
    send_email_use_case=_EMAIL_USE_CASE,
    send_push_use_case=_PUSH_USE_CASE,
    email_domain=settings.mock_email_domain,
    push_prefix=settings.mock_push_prefix,
)
_EVENT_CONSUMER = NotificationEventConsumer(
    bootstrap_servers=settings.kafka.bootstrap_servers,
    group_id=settings.consumer_group,
    topics=[
        "order-service.order.created",
        "order-service.order.confirmed",
        "delivery-service.delivery.assigned",
    ],
    processor=_EVENT_PROCESSOR,
    auto_offset_reset=settings.kafka.consumer_auto_offset_reset,
)


async def get_notification_repository() -> INotificationRepository:
    """Provide notification repository."""
    return _REPOSITORY


async def get_template_renderer() -> ITemplateRenderer:
    """Provide template renderer."""
    return _TEMPLATE_RENDERER


async def get_email_client() -> IEmailClient:
    """Provide email client."""
    return _EMAIL_CLIENT


async def get_push_client() -> IPushClient:
    """Provide push client."""
    return _PUSH_CLIENT


async def get_notification_event_publisher() -> INotificationEventPublisher:
    """Provide notification event publisher."""
    return _EVENT_PUBLISHER


async def get_send_email_use_case() -> SendEmailUseCase:
    """Provide send email use case."""
    return _EMAIL_USE_CASE


async def get_send_push_use_case() -> SendPushUseCase:
    """Provide send push use case."""
    return _PUSH_USE_CASE


async def get_get_notification_use_case() -> GetNotificationUseCase:
    """Provide get notification use case."""
    return GetNotificationUseCase(repository=_REPOSITORY)


async def get_list_notifications_use_case() -> ListNotificationsUseCase:
    """Provide list notifications use case."""
    return ListNotificationsUseCase(repository=_REPOSITORY)


def get_notification_event_consumer() -> NotificationEventConsumer:
    """Provide notification event consumer singleton."""
    return _EVENT_CONSUMER


def get_notification_event_processor() -> NotificationEventProcessor:
    """Provide event processor singleton."""
    return _EVENT_PROCESSOR


def reset_notification_state() -> None:
    """Reset singleton state for tests."""
    _REPOSITORY.clear()
    _EMAIL_CLIENT.clear()
    _PUSH_CLIENT.clear()
    _EVENT_PROCESSOR.clear()
