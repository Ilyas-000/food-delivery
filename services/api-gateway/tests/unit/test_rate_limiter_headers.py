"""Unit tests for rate-limit throttling response headers."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status

from src.middleware.rate_limiter import RateLimiter


def _request() -> SimpleNamespace:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))


@pytest.mark.unit
async def test_throttled_response_includes_standard_headers() -> None:
    redis = AsyncMock()
    redis.get.return_value = "1000"  # already over any limit -> rejected
    limiter = RateLimiter(redis)

    with pytest.raises(HTTPException) as exc_info:
        await limiter._check_and_raise(
            _request(),
            key="auth:global:ip:1.2.3.4:min",
            limit=5,
            window=60,
            message="Too many requests.",
            scope="auth_global_minute",
            burst=2,
        )

    exc = exc_info.value
    assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert exc.headers is not None
    assert exc.headers["Retry-After"] == "60"
    assert exc.headers["X-RateLimit-Remaining"] == "0"
    assert exc.headers["X-RateLimit-Limit"] == "7"


@pytest.mark.unit
def test_too_many_requests_omits_limit_header_when_unknown() -> None:
    exc = RateLimiter._too_many_requests("Cooldown active.", retry_after=30)

    assert exc.headers is not None
    assert exc.headers["Retry-After"] == "30"
    assert exc.headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Limit" not in exc.headers
