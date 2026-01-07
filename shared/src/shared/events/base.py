from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseEvent(BaseModel):
    """Event envelope shared across services."""

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    aggregate_id: str = Field(..., description="ID of the related entity")
    aggregate_type: str = Field(..., description="Type of aggregate (order, user, etc)")
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp (UTC)"
    )
    schema_version: int = Field(default=1, description="Event schema version")

    # Tracing
    correlation_id: UUID | None = Field(
        default=None, description="Correlation ID for distributed tracing"
    )
    causation_id: UUID | None = Field(
        default=None, description="ID of the command/event that caused this event"
    )

    # Meta
    user_id: str | None = Field(default=None, description="User who triggered this event")

    model_config = ConfigDict(extra="forbid")
