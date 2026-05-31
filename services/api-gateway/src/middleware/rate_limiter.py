"""Advanced rate limiting with Redis."""

import time

import structlog
from fastapi import HTTPException, Request, status
from shared.common.jwt import decode_token_unverified
from shared.common.redis import RedisClient

from src.config import settings
from src.observability import GatewayMetrics
from src.utils.ip import get_client_ip

logger = structlog.get_logger()


def _normalize_email_for_key(email: str | None) -> str | None:
    if not email:
        return None
    normalized = email.strip().lower()
    return normalized if normalized else None


class RateLimiter:
    """Advanced rate limiter using Redis."""

    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    @staticmethod
    def _get_metrics(request: Request) -> GatewayMetrics | None:
        return getattr(request.app.state, "gateway_metrics", None)

    @staticmethod
    def _too_many_requests(
        message: str,
        retry_after: int,
        *,
        limit: int | None = None,
        remaining: int = 0,
    ) -> HTTPException:
        """Build a 429 response with standard throttling headers."""
        headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Remaining": str(remaining),
        }
        if limit is not None:
            headers["X-RateLimit-Limit"] = str(limit)
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": message,
                    "retry_after": retry_after,
                }
            },
            headers=headers,
        )

    async def _check_limit(
        self,
        key: str,
        limit: int,
        window: int,
        burst: int | None = None,
    ) -> tuple[bool, int]:
        """Check if rate limit is exceeded using sliding window counter."""
        current_time = int(time.time())
        window_key = f"ratelimit:{key}:{current_time // window}"

        count = await self.redis.get(window_key)
        current_count = int(count) if count else 0
        effective_limit = limit + (burst or 0)

        if current_count >= effective_limit:
            return False, 0

        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window * 2)
        await pipe.execute()

        return True, effective_limit - current_count - 1

    async def _check_and_raise(
        self,
        request: Request,
        key: str,
        limit: int,
        window: int,
        message: str,
        scope: str,
        burst: int | None = None,
    ) -> None:
        """Check limit and raise HTTPException if exceeded."""
        allowed, _ = await self._check_limit(key, limit, window, burst)
        metrics = self._get_metrics(request)
        if metrics is not None:
            metrics.record_rate_limit_decision(scope, "allowed" if allowed else "rejected")
        if not allowed:
            raise self._too_many_requests(
                message,
                retry_after=window,
                limit=limit + (burst or 0),
            )

    async def _record_failure(self, key: str, window: int) -> None:
        """Record a failed attempt for progressive backoff."""
        current_time = int(time.time())
        failure_key = f"failures:{key}:{current_time // window}"

        pipe = self.redis.pipeline()
        pipe.incr(failure_key)
        pipe.expire(failure_key, window * 2)
        await pipe.execute()

    async def _get_failure_count(self, key: str, window: int) -> int:
        """Get number of failures in time window."""
        current_time = int(time.time())
        failure_key = f"failures:{key}:{current_time // window}"
        count = await self.redis.get(failure_key)
        return int(count) if count else 0

    async def _is_in_cooldown(self, key: str) -> tuple[bool, int]:
        """Check if key is in cooldown period."""
        cooldown_key = f"cooldown:{key}"
        ttl = await self.redis.ttl(cooldown_key)
        return (True, ttl) if ttl > 0 else (False, 0)

    async def _set_cooldown(self, key: str, duration: int) -> None:
        """Set cooldown period."""
        cooldown_key = f"cooldown:{key}"
        await self.redis.setex(cooldown_key, duration, "1")
        logger.warning("Cooldown activated", key=key, duration=duration)

    async def check_login_rate_limit(self, request: Request, email: str | None = None) -> None:
        """Check login rate limits with progressive backoff."""
        client_ip = get_client_ip(request)
        normalized_email = _normalize_email_for_key(email)

        # Check cooldown
        in_cooldown, remaining = await self._is_in_cooldown(f"login:ip:{client_ip}")
        if in_cooldown:
            metrics = self._get_metrics(request)
            if metrics is not None:
                metrics.record_rate_limit_decision("login_cooldown", "rejected")
            raise self._too_many_requests(
                f"Too many failed attempts. Try again in {remaining} seconds.",
                retry_after=remaining,
            )

        # Per-IP limits
        await self._check_and_raise(
            request,
            f"login:ip:{client_ip}:min",
            settings.login_per_ip_minute,
            60,
            "Too many login attempts from this IP.",
            scope="login_ip_minute",
        )
        await self._check_and_raise(
            request,
            f"login:ip:{client_ip}:hour",
            settings.login_per_ip_hour,
            3600,
            "Too many login attempts from this IP.",
            scope="login_ip_hour",
        )

        # Per-account limits
        if normalized_email:
            await self._check_and_raise(
                request,
                f"login:account:{normalized_email}:min",
                settings.login_per_account_minute,
                60,
                "Too many login attempts for this account.",
                scope="login_account_minute",
            )
            await self._check_and_raise(
                request,
                f"login:account:{normalized_email}:hour",
                settings.login_per_account_hour,
                3600,
                "Too many login attempts for this account.",
                scope="login_account_hour",
            )
            await self._check_and_raise(
                request,
                f"login:ip_account:{client_ip}:{normalized_email}:min",
                settings.login_per_ip_account_minute,
                60,
                "Too many login attempts.",
                scope="login_ip_account_minute",
            )

    async def record_login_failure(self, request: Request, email: str | None = None) -> None:
        """Record failed login and activate cooldown if threshold exceeded."""
        client_ip = get_client_ip(request)

        await self._record_failure(f"login:ip:{client_ip}", settings.login_max_fails_window)

        failure_count = await self._get_failure_count(
            f"login:ip:{client_ip}",
            settings.login_max_fails_window,
        )

        if failure_count >= settings.login_max_fails_count:
            await self._set_cooldown(f"login:ip:{client_ip}", settings.login_cooldown_duration)
            metrics = self._get_metrics(request)
            if metrics is not None:
                metrics.record_rate_limit_cooldown("login_ip")

    async def check_refresh_rate_limit(
        self,
        request: Request,
        refresh_token: str,
        user_id: str | None = None,
    ) -> None:
        """Check refresh token rate limits."""
        client_ip = get_client_ip(request)

        # Extract JTI from refresh token
        try:
            unverified = decode_token_unverified(refresh_token)
            jti = unverified.get("jti")
        except Exception:
            jti = None

        # Per-JTI limits
        if jti:
            await self._check_and_raise(
                request,
                f"refresh:jti:{jti}:min",
                settings.refresh_per_jti_minute,
                60,
                "Too many refresh attempts with this token.",
                scope="refresh_jti_minute",
            )
            await self._check_and_raise(
                request,
                f"refresh:jti:{jti}:hour",
                settings.refresh_per_jti_hour,
                3600,
                "Too many refresh attempts.",
                scope="refresh_jti_hour",
            )

        # Per-user limits
        if user_id:
            await self._check_and_raise(
                request,
                f"refresh:user:{user_id}:min",
                settings.refresh_per_user_minute,
                60,
                "Too many refresh attempts.",
                scope="refresh_user_minute",
            )

        # Per-IP limits
        await self._check_and_raise(
            request,
            f"refresh:ip:{client_ip}:min",
            settings.refresh_per_ip_minute,
            60,
            "Too many refresh attempts from this IP.",
            scope="refresh_ip_minute",
        )
        await self._check_and_raise(
            request,
            f"refresh:ip:{client_ip}:hour",
            settings.refresh_per_ip_hour,
            3600,
            "Too many refresh attempts from this IP.",
            scope="refresh_ip_hour",
        )

    async def check_auth_global_rate_limit(self, request: Request) -> None:
        """Check global auth endpoint rate limit."""
        client_ip = get_client_ip(request)

        await self._check_and_raise(
            request,
            f"auth:global:ip:{client_ip}:min",
            settings.auth_global_per_ip_minute,
            60,
            "Too many requests to authentication endpoints.",
            scope="auth_global_minute",
            burst=settings.auth_global_burst,
        )
        await self._check_and_raise(
            request,
            f"auth:global:ip:{client_ip}:hour",
            settings.auth_global_per_ip_hour,
            3600,
            "Too many requests to authentication endpoints.",
            scope="auth_global_hour",
        )
