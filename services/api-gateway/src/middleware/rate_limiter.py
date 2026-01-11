"""Advanced rate limiting with Redis.

Implements sophisticated rate limiting strategies:
- Per IP, per account, per IP+account combinations
- Progressive backoff on failed login attempts
- Per refresh token JTI tracking
- Burst allowance for legitimate users
- Multiple time windows (minute, hour)
"""

import time

import structlog
from fastapi import HTTPException, Request, status
from shared.common.jwt import decode_token_unverified
from shared.common.redis import RedisClient

from ..config import settings

logger = structlog.get_logger()


class RateLimiter:
    """Advanced rate limiter using Redis."""

    def __init__(self, redis: RedisClient) -> None:
        """Initialize rate limiter.

        Args:
            redis: Redis client
        """
        self.redis = redis

    async def _check_limit(
        self,
        key: str,
        limit: int,
        window: int,
        burst: int | None = None,
    ) -> tuple[bool, int]:
        """Check if rate limit is exceeded.

        Uses sliding window counter algorithm.

        Args:
            key: Redis key for this limit
            limit: Maximum requests allowed
            window: Time window in seconds
            burst: Optional burst allowance (tokens added immediately)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = int(time.time())
        window_key = f"ratelimit:{key}:{current_time // window}"

        # Get current count
        count = await self.redis.get(window_key)
        current_count = int(count) if count else 0

        # Apply burst allowance
        effective_limit = limit + (burst or 0)

        if current_count >= effective_limit:
            return False, 0

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window * 2)  # Keep for 2 windows
        await pipe.execute()

        remaining = effective_limit - current_count - 1
        return True, remaining

    async def _record_failure(self, key: str, window: int) -> None:
        """Record a failed attempt (for progressive backoff).

        Args:
            key: Redis key prefix
            window: Time window in seconds
        """
        current_time = int(time.time())
        failure_key = f"failures:{key}:{current_time // window}"

        pipe = self.redis.pipeline()
        pipe.incr(failure_key)
        pipe.expire(failure_key, window * 2)
        await pipe.execute()

    async def _get_failure_count(self, key: str, window: int) -> int:
        """Get number of failures in time window.

        Args:
            key: Redis key prefix
            window: Time window in seconds

        Returns:
            Number of failures
        """
        current_time = int(time.time())
        failure_key = f"failures:{key}:{current_time // window}"
        count = await self.redis.get(failure_key)
        return int(count) if count else 0

    async def _is_in_cooldown(self, key: str) -> tuple[bool, int]:
        """Check if key is in cooldown period.

        Args:
            key: Redis key for cooldown

        Returns:
            Tuple of (is_in_cooldown, remaining_seconds)
        """
        cooldown_key = f"cooldown:{key}"
        ttl = await self.redis.ttl(cooldown_key)
        if ttl > 0:
            return True, ttl
        return False, 0

    async def _set_cooldown(self, key: str, duration: int) -> None:
        """Set cooldown period.

        Args:
            key: Redis key for cooldown
            duration: Cooldown duration in seconds
        """
        cooldown_key = f"cooldown:{key}"
        await self.redis.setex(cooldown_key, duration, "1")
        logger.warning("Cooldown activated", key=key, duration=duration)

    async def check_login_rate_limit(self, request: Request, email: str | None = None) -> None:
        """Check login rate limits with progressive backoff.

        Limits:
        - per_ip: 10/min, 100/hour
        - per_account: 5/min, 20/hour (if email provided)
        - per_ip_account: 3/min (if email provided)
        - on_fail: 5 fails/10min -> 15min cooldown

        Args:
            request: FastAPI request
            email: User email (if available)

        Raises:
            HTTPException: If rate limit exceeded
        """
        client_ip = request.client.host if request.client else "unknown"

        # Check IP cooldown (progressive backoff)
        in_cooldown, remaining = await self._is_in_cooldown(f"login:ip:{client_ip}")
        if in_cooldown:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many failed login attempts. Try again in {remaining} seconds.",
                        "retry_after": remaining,
                    }
                },
            )

        # Check per-IP rate limits
        allowed, remaining_min = await self._check_limit(
            f"login:ip:{client_ip}:min",
            settings.login_per_ip_minute,
            60,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many login attempts from this IP. Try again later.",
                        "retry_after": 60,
                    }
                },
            )

        allowed, _ = await self._check_limit(
            f"login:ip:{client_ip}:hour",
            settings.login_per_ip_hour,
            3600,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many login attempts from this IP. Try again in an hour.",
                        "retry_after": 3600,
                    }
                },
            )

        # Check per-account limits (if email provided)
        if email:
            allowed, _ = await self._check_limit(
                f"login:account:{email}:min",
                settings.login_per_account_minute,
                60,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many login attempts for this account.",
                            "retry_after": 60,
                        }
                    },
                )

            allowed, _ = await self._check_limit(
                f"login:account:{email}:hour",
                settings.login_per_account_hour,
                3600,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many login attempts for this account.",
                            "retry_after": 3600,
                        }
                    },
                )

            # Check per-IP+account combination
            allowed, _ = await self._check_limit(
                f"login:ip_account:{client_ip}:{email}:min",
                settings.login_per_ip_account_minute,
                60,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many login attempts. Please try again later.",
                            "retry_after": 60,
                        }
                    },
                )

    async def record_login_failure(self, request: Request, email: str | None = None) -> None:
        """Record failed login and activate cooldown if threshold exceeded.

        Args:
            request: FastAPI request
            email: User email (if available)
        """
        client_ip = request.client.host if request.client else "unknown"

        # Record failure
        await self._record_failure(
            f"login:ip:{client_ip}",
            settings.login_max_fails_window,
        )

        # Check if cooldown should be activated
        failure_count = await self._get_failure_count(
            f"login:ip:{client_ip}",
            settings.login_max_fails_window,
        )

        if failure_count >= settings.login_max_fails_count:
            await self._set_cooldown(
                f"login:ip:{client_ip}",
                settings.login_cooldown_duration,
            )

    async def check_refresh_rate_limit(
        self,
        request: Request,
        refresh_token: str,
        user_id: str | None = None,
    ) -> None:
        """Check refresh token rate limits.

        Limits:
        - per_refresh_jti: 10/min, 60/hour
        - per_user_id: 30/min, 300/hour
        - per_ip: 60/min, 1000/hour

        Args:
            request: FastAPI request
            refresh_token: Refresh token
            user_id: User ID (if decoded successfully)

        Raises:
            HTTPException: If rate limit exceeded
        """
        client_ip = request.client.host if request.client else "unknown"

        # Extract JTI from refresh token (without verification)
        try:
            unverified = decode_token_unverified(refresh_token)
            jti = unverified.get("jti")
        except Exception:
            jti = None

        # Check per-JTI limits (if available)
        if jti:
            allowed, _ = await self._check_limit(
                f"refresh:jti:{jti}:min",
                settings.refresh_per_jti_minute,
                60,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many refresh attempts with this token.",
                            "retry_after": 60,
                        }
                    },
                )

            allowed, _ = await self._check_limit(
                f"refresh:jti:{jti}:hour",
                settings.refresh_per_jti_hour,
                3600,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many refresh attempts.",
                            "retry_after": 3600,
                        }
                    },
                )

        # Check per-user limits (if user_id available)
        if user_id:
            allowed, _ = await self._check_limit(
                f"refresh:user:{user_id}:min",
                settings.refresh_per_user_minute,
                60,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many refresh attempts.",
                            "retry_after": 60,
                        }
                    },
                )

        # Check per-IP limits
        allowed, _ = await self._check_limit(
            f"refresh:ip:{client_ip}:min",
            settings.refresh_per_ip_minute,
            60,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many refresh attempts from this IP.",
                        "retry_after": 60,
                    }
                },
            )

        allowed, _ = await self._check_limit(
            f"refresh:ip:{client_ip}:hour",
            settings.refresh_per_ip_hour,
            3600,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many refresh attempts from this IP.",
                        "retry_after": 3600,
                    }
                },
            )

    async def check_auth_global_rate_limit(self, request: Request) -> None:
        """Check global auth endpoint rate limit.

        Applies to all /auth/* endpoints.

        Limits:
        - per_ip: 60/min (burst 20), 1000/hour

        Args:
            request: FastAPI request

        Raises:
            HTTPException: If rate limit exceeded
        """
        client_ip = request.client.host if request.client else "unknown"

        # Check per-minute with burst
        allowed, _ = await self._check_limit(
            f"auth:global:ip:{client_ip}:min",
            settings.auth_global_per_ip_minute,
            60,
            burst=settings.auth_global_burst,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests to authentication endpoints.",
                        "retry_after": 60,
                    }
                },
            )

        # Check per-hour
        allowed, _ = await self._check_limit(
            f"auth:global:ip:{client_ip}:hour",
            settings.auth_global_per_ip_hour,
            3600,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests to authentication endpoints.",
                        "retry_after": 3600,
                    }
                },
            )
