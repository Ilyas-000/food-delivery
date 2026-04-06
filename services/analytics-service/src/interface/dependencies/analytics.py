"""Analytics dependency providers."""

from src.application.interfaces.analytics_repository import IAnalyticsRepository
from src.application.use_cases.get_overview import GetAnalyticsOverviewUseCase
from src.application.use_cases.ingest_event import IngestAnalyticsEventUseCase
from src.application.use_cases.list_events import ListAnalyticsEventsUseCase
from src.config import settings
from src.infrastructure.consumers.event_consumer import AnalyticsEventConsumer
from src.infrastructure.consumers.processor import AnalyticsEventProcessor
from src.infrastructure.repositories.clickhouse_analytics_repository import (
    ClickHouseAnalyticsRepository,
)
from src.infrastructure.repositories.in_memory_analytics_repository import (
    InMemoryAnalyticsRepository,
)

_MEMORY_REPOSITORY = InMemoryAnalyticsRepository()
_CLICKHOUSE_REPOSITORY = ClickHouseAnalyticsRepository(
    host=settings.clickhouse.host,
    http_port=settings.clickhouse.http_port,
    user=settings.clickhouse.user,
    password=settings.clickhouse.password,
    database=settings.clickhouse.database,
    table=settings.clickhouse_table,
    timeout_seconds=settings.clickhouse_timeout_seconds,
)


def _get_repository_instance() -> IAnalyticsRepository:
    if settings.storage_backend == "clickhouse":
        return _CLICKHOUSE_REPOSITORY
    return _MEMORY_REPOSITORY


_INGEST_USE_CASE = IngestAnalyticsEventUseCase(repository=_get_repository_instance())
_EVENT_PROCESSOR = AnalyticsEventProcessor(ingest_event_use_case=_INGEST_USE_CASE)
_EVENT_CONSUMER = AnalyticsEventConsumer(
    bootstrap_servers=settings.kafka.bootstrap_servers,
    group_id=settings.consumer_group,
    topics=[
        "order-service.order.created",
        "order-service.order.confirmed",
        "delivery-service.delivery.assigned",
        "notification-service.notification.email_sent",
        "notification-service.notification.push_sent",
    ],
    processor=_EVENT_PROCESSOR,
    auto_offset_reset=settings.kafka.consumer_auto_offset_reset,
)


async def get_analytics_repository() -> IAnalyticsRepository:
    """Provide analytics repository."""
    return _get_repository_instance()


async def get_ingest_analytics_event_use_case() -> IngestAnalyticsEventUseCase:
    """Provide ingest analytics use case."""
    return IngestAnalyticsEventUseCase(repository=_get_repository_instance())


async def get_get_analytics_overview_use_case() -> GetAnalyticsOverviewUseCase:
    """Provide overview use case."""
    return GetAnalyticsOverviewUseCase(repository=_get_repository_instance())


async def get_list_analytics_events_use_case() -> ListAnalyticsEventsUseCase:
    """Provide event listing use case."""
    return ListAnalyticsEventsUseCase(repository=_get_repository_instance())


def get_analytics_event_consumer() -> AnalyticsEventConsumer:
    """Provide analytics event consumer singleton."""
    return _EVENT_CONSUMER


def get_analytics_repository_instance() -> IAnalyticsRepository:
    """Expose repository singleton for lifespan hooks."""
    return _get_repository_instance()


def reset_analytics_state() -> None:
    """Reset singleton state for tests."""
    _MEMORY_REPOSITORY.clear()
