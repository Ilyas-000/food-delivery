"""Gateway-specific Prometheus instrumentation."""

from prometheus_client import Counter, Gauge
from shared.observability.prometheus import ServiceMetrics


class GatewayMetrics(ServiceMetrics):
    """Prometheus metrics registry for API Gateway internals."""

    def __init__(self, service_name: str) -> None:
        super().__init__(service_name)
        self.circuit_breaker_state = Gauge(
            "food_delivery_gateway_circuit_breaker_state",
            "Current circuit breaker state for each downstream service.",
            labelnames=("downstream_service", "state"),
            registry=self.registry,
        )
        self.circuit_breaker_state_changes_total = Counter(
            "food_delivery_gateway_circuit_breaker_state_changes_total",
            "Number of circuit breaker state transitions.",
            labelnames=("downstream_service", "state"),
            registry=self.registry,
        )
        self.circuit_breaker_failures_total = Counter(
            "food_delivery_gateway_circuit_breaker_failures_total",
            "Upstream failures recorded by circuit breakers.",
            labelnames=("downstream_service",),
            registry=self.registry,
        )
        self.circuit_breaker_rejections_total = Counter(
            "food_delivery_gateway_circuit_breaker_rejections_total",
            "Requests rejected because the circuit breaker is open.",
            labelnames=("downstream_service",),
            registry=self.registry,
        )
        self.rate_limit_decisions_total = Counter(
            "food_delivery_gateway_rate_limit_decisions_total",
            "Rate limiter decisions by scope and result.",
            labelnames=("scope", "result"),
            registry=self.registry,
        )
        self.rate_limit_cooldowns_total = Counter(
            "food_delivery_gateway_rate_limit_cooldowns_total",
            "Cooldown activations triggered by failed login bursts.",
            labelnames=("scope",),
            registry=self.registry,
        )

    def set_circuit_breaker_state(self, downstream_service: str, state: str) -> None:
        """Update one-hot state gauge for a downstream service."""
        for candidate in ("closed", "open", "half_open"):
            value = 1 if candidate == state else 0
            self.circuit_breaker_state.labels(
                downstream_service=downstream_service,
                state=candidate,
            ).set(value)

    def record_circuit_breaker_state_change(self, downstream_service: str, state: str) -> None:
        """Record a circuit breaker state transition."""
        self.circuit_breaker_state_changes_total.labels(
            downstream_service=downstream_service,
            state=state,
        ).inc()
        self.set_circuit_breaker_state(downstream_service, state)

    def record_circuit_breaker_failure(self, downstream_service: str) -> None:
        """Record a downstream failure observed by a circuit breaker."""
        self.circuit_breaker_failures_total.labels(downstream_service=downstream_service).inc()

    def record_circuit_breaker_rejection(self, downstream_service: str) -> None:
        """Record a request rejected by an open circuit breaker."""
        self.circuit_breaker_rejections_total.labels(downstream_service=downstream_service).inc()

    def record_rate_limit_decision(self, scope: str, result: str) -> None:
        """Record whether a rate-limit check allowed or rejected traffic."""
        self.rate_limit_decisions_total.labels(scope=scope, result=result).inc()

    def record_rate_limit_cooldown(self, scope: str) -> None:
        """Record a cooldown activation."""
        self.rate_limit_cooldowns_total.labels(scope=scope).inc()
