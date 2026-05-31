"""Circuit Breaker middleware to protect against cascading failures.

Circuit Breaker Pattern:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, reject requests immediately
- HALF_OPEN: Testing if service recovered

This protects the gateway from waiting on failed services.
"""

import time
from collections.abc import Awaitable, Callable
from enum import Enum

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from src.observability import GatewayMetrics


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Too many failures, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for a single service."""

    def __init__(
        self,
        service_name: str,
        gateway_metrics: GatewayMetrics,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            service_name: Name of the protected service
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.gateway_metrics = gateway_metrics

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.logger = structlog.get_logger()
        self.gateway_metrics.set_circuit_breaker_state(self.service_name, self.state.value)

    def _transition_to(self, state: CircuitState) -> None:
        """Transition circuit breaker state and publish metrics."""
        if self.state == state:
            return
        self.state = state
        self.gateway_metrics.record_circuit_breaker_state_change(
            self.service_name,
            state.value,
        )

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        if self.state == CircuitState.CLOSED:
            return False

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.recovery_timeout
            ):
                self.logger.info(
                    "Circuit breaker entering HALF_OPEN",
                    service=self.service_name,
                )
                self._transition_to(CircuitState.HALF_OPEN)
                return False
            return True

        # HALF_OPEN: allow one request through
        return False

    def record_success(self) -> None:
        """Record successful request.

        Resets failure count on any success to prevent accumulation of old failures.
        """
        if self.state == CircuitState.HALF_OPEN:
            self.logger.info(
                "Circuit breaker recovery successful",
                service=self.service_name,
            )
            self._transition_to(CircuitState.CLOSED)
            self.last_failure_time = None

        self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.gateway_metrics.record_circuit_breaker_failure(self.service_name)

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.logger.warning(
                    "Circuit breaker opened",
                    service=self.service_name,
                    failure_count=self.failure_count,
                )
                self._transition_to(CircuitState.OPEN)


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Middleware to apply circuit breaker to service calls."""

    def __init__(
        self,
        app: ASGIApp,
        gateway_metrics: GatewayMetrics,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        """Initialize middleware.

        Args:
            app: FastAPI application
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        super().__init__(app)
        self.breakers: dict[str, CircuitBreaker] = {}
        self.gateway_metrics = gateway_metrics
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def _get_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.breakers:
            self.breakers[service_name] = CircuitBreaker(
                service_name=service_name,
                gateway_metrics=self.gateway_metrics,
                failure_threshold=self.failure_threshold,
                recovery_timeout=self.recovery_timeout,
            )
        return self.breakers[service_name]

    def _extract_service_name(self, path: str) -> str | None:
        """Extract service name from request path.

        Examples:
            /api/v1/users/... -> user-service
            /api/v1/restaurants/... -> restaurant-service
            /api/v1/orders/... -> order-service
        """
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
            resource = parts[2]
            # Map resource to service name
            service_map = {
                "auth": "user-service",
                "users": "user-service",
                "restaurants": "restaurant-service",
                "orders": "order-service",
                "payments": "payment-service",
                "deliveries": "delivery-service",
                "analytics": "analytics-service",
                "reviews": "review-service",
            }
            return service_map.get(resource)
        return None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Apply circuit breaker logic."""
        service_name = self._extract_service_name(request.url.path)

        # Skip circuit breaker for non-service paths (health checks, etc.)
        if not service_name:
            return await call_next(request)

        breaker = self._get_breaker(service_name)

        # Check if circuit is open
        if breaker.is_open():
            self.gateway_metrics.record_circuit_breaker_rejection(service_name)
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": f"{service_name} is currently unavailable",
                        "details": "Circuit breaker is open. Service is experiencing issues.",
                    }
                },
            )

        try:
            # Process request
            response: Response = await call_next(request)

            # Record success for 2xx responses
            if 200 <= response.status_code < 300:
                breaker.record_success()
            # Record failure for 5xx errors
            elif response.status_code >= 500:
                breaker.record_failure()

            return response

        except Exception:
            # Record failure on exception
            breaker.record_failure()
            raise
