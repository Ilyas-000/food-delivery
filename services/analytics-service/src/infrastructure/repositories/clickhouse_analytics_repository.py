"""ClickHouse-backed analytics repository."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any
from uuid import UUID

import httpx
import structlog

from src.application.dto.analytics import AnalyticsOverviewDTO
from src.application.interfaces.analytics_repository import IAnalyticsRepository
from src.domain.entities.analytics_event import AnalyticsEvent

logger = structlog.get_logger(__name__)


class ClickHouseAnalyticsRepository(IAnalyticsRepository):
    """Persist analytics events in ClickHouse via HTTP API."""

    def __init__(
        self,
        *,
        host: str,
        http_port: int,
        user: str,
        password: str,
        database: str,
        table: str,
        timeout_seconds: float,
    ) -> None:
        self._base_url = f"http://{host}:{http_port}"
        self._auth: tuple[str, str] | None
        if password or user not in {"", "default"}:
            self._auth = (user, password)
        else:
            self._auth = None
        self._database = database
        self._table = table
        self._timeout_seconds = timeout_seconds
        self._client: httpx.AsyncClient | None = None
        self._ready = False

    async def start(self) -> None:
        """Initialize ClickHouse client and ensure schema."""
        if self._client is not None:
            return

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            auth=self._auth,
            trust_env=False,
        )
        await self._execute(
            f"CREATE DATABASE IF NOT EXISTS {self._database}",
            use_database=False,
        )
        await self._execute(self._build_create_table_query())
        await self._execute("SELECT 1")
        self._ready = True
        logger.info("analytics.clickhouse.started", database=self._database, table=self._table)

    async def stop(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._ready = False

    def is_ready(self) -> bool:
        """Return readiness state."""
        return self._ready and self._client is not None

    async def save(self, event: AnalyticsEvent) -> AnalyticsEvent:
        """Insert analytics event row."""
        payload = json.dumps(self._serialize_row(event), ensure_ascii=True)
        await self._execute(
            f"INSERT INTO {self._database}.{self._table} FORMAT JSONEachRow",
            content=f"{payload}\n",
        )
        return event

    async def list_events(
        self,
        *,
        event_type: str | None,
        limit: int,
    ) -> list[AnalyticsEvent]:
        """Return recent analytics events."""
        where_clause = ""
        if event_type:
            where_clause = f"WHERE event_type = {self._escape_literal(event_type)}"
        query = "\n".join(
            [
                "SELECT",
                "    event_id,",
                "    event_type,",
                "    aggregate_id,",
                "    aggregate_type,",
                "    occurred_at,",
                "    user_id,",
                "    order_id,",
                "    restaurant_id,",
                "    amount,",
                "    currency,",
                "    notification_type,",
                "    recipient,",
                "    template_name,",
                "    source_event_type,",
                "    payload_json",
                f"FROM {self._database}.{self._table}",
                where_clause,
                "ORDER BY occurred_at DESC",
                f"LIMIT {limit}",
                "FORMAT JSONEachRow",
            ]
        )
        rows = await self._execute_json_each_row(query)
        return [self._deserialize_row(row) for row in rows]

    async def get_overview(
        self,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> AnalyticsOverviewDTO:
        """Return operational overview from ClickHouse aggregates."""
        where_clause = self._build_time_window_clause(date_from=date_from, date_to=date_to)
        query = "\n".join(
            [
                "SELECT",
                "    count() AS total_events,",
                "    countIf(event_type = 'order-service.order.created') AS orders_created,",
                "    countIf(event_type = 'order-service.order.confirmed') AS orders_confirmed,",
                "    countIf(event_type = 'delivery-service.delivery.assigned') "
                "AS deliveries_assigned,",
                "    countIf(event_type = 'notification-service.notification.email_sent') "
                "AS emails_sent,",
                "    countIf(event_type = 'notification-service.notification.push_sent') "
                "AS pushes_sent,",
                "    sumIf(amount, event_type = 'order-service.order.created') "
                "AS gross_revenue,",
                "    uniqExactIf(",
                "        user_id,",
                "        event_type = 'order-service.order.created' AND user_id IS NOT NULL",
                "    ) AS unique_customers",
                f"FROM {self._database}.{self._table}",
                where_clause,
                "FORMAT JSONEachRow",
            ]
        )
        rows = await self._execute_json_each_row(query)
        row = rows[0] if rows else {}
        emails_sent = int(row.get("emails_sent", 0))
        pushes_sent = int(row.get("pushes_sent", 0))
        revenue_raw = row.get("gross_revenue")
        revenue = Decimal(str(revenue_raw or 0)).quantize(Decimal("0.01"))
        return AnalyticsOverviewDTO(
            total_events=int(row.get("total_events", 0)),
            orders_created=int(row.get("orders_created", 0)),
            orders_confirmed=int(row.get("orders_confirmed", 0)),
            deliveries_assigned=int(row.get("deliveries_assigned", 0)),
            emails_sent=emails_sent,
            pushes_sent=pushes_sent,
            notifications_sent=emails_sent + pushes_sent,
            gross_revenue=revenue,
            unique_customers=int(row.get("unique_customers", 0)),
            date_from=date_from,
            date_to=date_to,
        )

    async def _execute(
        self,
        query: str,
        *,
        content: str | None = None,
        use_database: bool = True,
    ) -> str:
        if self._client is None:
            msg = "ClickHouse client is not initialized"
            raise RuntimeError(msg)
        params: dict[str, str] = {}
        if use_database:
            params["database"] = self._database
        if content is not None:
            params["query"] = query
        response = await self._client.post(
            "/",
            params=params,
            content=content if content is not None else query,
        )
        response.raise_for_status()
        return response.text

    async def _execute_json_each_row(self, query: str) -> list[dict[str, Any]]:
        response_text = await self._execute(query)
        return [json.loads(line) for line in response_text.splitlines() if line.strip()]

    def _build_create_table_query(self) -> str:
        return f"""
            CREATE TABLE IF NOT EXISTS {self._database}.{self._table} (
                event_id UUID,
                event_type LowCardinality(String),
                aggregate_id String,
                aggregate_type LowCardinality(String),
                occurred_at DateTime64(3, 'UTC'),
                user_id Nullable(String),
                order_id Nullable(String),
                restaurant_id Nullable(String),
                amount Nullable(Float64),
                currency Nullable(String),
                notification_type Nullable(String),
                recipient Nullable(String),
                template_name Nullable(String),
                source_event_type Nullable(String),
                payload_json String
            )
            ENGINE = MergeTree
            ORDER BY (event_type, occurred_at, aggregate_id)
        """

    def _serialize_row(self, event: AnalyticsEvent) -> dict[str, Any]:
        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "occurred_at": event.occurred_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "user_id": event.user_id,
            "order_id": event.order_id,
            "restaurant_id": event.restaurant_id,
            "amount": float(event.amount) if event.amount is not None else None,
            "currency": event.currency,
            "notification_type": event.notification_type,
            "recipient": event.recipient,
            "template_name": event.template_name,
            "source_event_type": event.source_event_type,
            "payload_json": json.dumps(event.payload, ensure_ascii=True, sort_keys=True),
        }

    def _deserialize_row(self, row: dict[str, Any]) -> AnalyticsEvent:
        payload_raw = row.get("payload_json", "{}")
        return AnalyticsEvent.create(
            event_id=UUID(str(row["event_id"])),
            event_type=row["event_type"],
            aggregate_id=row["aggregate_id"],
            aggregate_type=row["aggregate_type"],
            occurred_at=self._parse_datetime(str(row["occurred_at"])),
            user_id=row.get("user_id"),
            order_id=row.get("order_id"),
            restaurant_id=row.get("restaurant_id"),
            amount=Decimal(str(row["amount"])) if row.get("amount") is not None else None,
            currency=row.get("currency"),
            notification_type=row.get("notification_type"),
            recipient=row.get("recipient"),
            template_name=row.get("template_name"),
            source_event_type=row.get("source_event_type"),
            payload=json.loads(payload_raw),
        )

    def _build_time_window_clause(
        self,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> str:
        conditions: list[str] = []
        if date_from is not None:
            conditions.append(f"occurred_at >= {self._escape_datetime(date_from)}")
        if date_to is not None:
            conditions.append(f"occurred_at <= {self._escape_datetime(date_to)}")
        if not conditions:
            return ""
        return "WHERE " + " AND ".join(conditions)

    def _escape_datetime(self, value: datetime) -> str:
        return self._escape_literal(value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S.%f"))

    def _escape_literal(self, value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"

    def _parse_datetime(self, value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
