from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseEvent(BaseModel):
    """Event envelope shared across services."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: int = 1

    # Tracing
    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    # Meta
    user_id: str | None = None

    model_config = ConfigDict(extra="forbid")
