"""Analytics API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.application.use_cases.get_overview import GetAnalyticsOverviewUseCase
from src.application.use_cases.list_events import ListAnalyticsEventsUseCase
from src.interface.api.v1.schemas.analytics import (
    AnalyticsEventListResponse,
    AnalyticsOverviewResponse,
)
from src.interface.dependencies.analytics import (
    get_get_analytics_overview_use_case,
    get_list_analytics_events_use_case,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse, status_code=status.HTTP_200_OK)
async def get_analytics_overview(
    use_case: Annotated[GetAnalyticsOverviewUseCase, Depends(get_get_analytics_overview_use_case)],
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
) -> AnalyticsOverviewResponse:
    """Return operational analytics overview."""
    result = await use_case.execute(date_from=date_from, date_to=date_to)
    return AnalyticsOverviewResponse.from_dto(result)


@router.get("/events", response_model=AnalyticsEventListResponse, status_code=status.HTTP_200_OK)
async def list_analytics_events(
    use_case: Annotated[ListAnalyticsEventsUseCase, Depends(get_list_analytics_events_use_case)],
    event_type: Annotated[str | None, Query(min_length=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AnalyticsEventListResponse:
    """Return recent analytics events."""
    result = await use_case.execute(event_type=event_type, limit=limit)
    return AnalyticsEventListResponse.from_dto(result)
