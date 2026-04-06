"""Auth dependencies for review-service."""

from typing import Annotated
from uuid import UUID

from fastapi import Header

from src.domain.exceptions.base import ReviewUnauthorizedError


async def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> UUID:
    """Resolve current user id from gateway header."""
    if not x_user_id:
        raise ReviewUnauthorizedError("missing X-User-ID header")
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise ReviewUnauthorizedError("invalid X-User-ID header") from exc
