"""Prometheus instrumentation helpers for FastAPI services."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware


class ServiceMetrics:
    """Prometheus registry and shared HTTP metrics for a single service."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self.registry = CollectorRegistry(auto_describe=True)
        self.http_requests_total = Counter(
            "food_delivery_http_requests_total",
            "Total HTTP requests processed by the service.",
            labelnames=("service", "method", "path", "status_code"),
            registry=self.registry,
        )
        self.http_request_duration_seconds = Histogram(
            "food_delivery_http_request_duration_seconds",
            "HTTP request duration in seconds.",
            labelnames=("service", "method", "path"),
            registry=self.registry,
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
        self.http_requests_in_progress = Gauge(
            "food_delivery_http_requests_in_progress",
            "HTTP requests currently being processed.",
            labelnames=("service",),
            registry=self.registry,
        )

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Store aggregated HTTP request metrics."""
        self.http_requests_total.labels(
            service=self.service_name,
            method=method,
            path=path,
            status_code=str(status_code),
        ).inc()
        self.http_request_duration_seconds.labels(
            service=self.service_name,
            method=method,
            path=path,
        ).observe(duration_seconds)

    def render(self) -> bytes:
        """Render metrics in Prometheus text format."""
        payload: bytes = generate_latest(self.registry)
        return payload

    def create_counter(
        self,
        name: str,
        documentation: str,
        *,
        labelnames: tuple[str, ...] = (),
    ) -> Counter:
        """Create a service-scoped Prometheus counter on the service registry."""
        return Counter(
            name,
            documentation,
            labelnames=labelnames,
            registry=self.registry,
        )


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Collect per-request Prometheus metrics."""

    def __init__(
        self,
        app: FastAPI,
        metrics: ServiceMetrics,
        ignored_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.metrics = metrics
        self.ignored_paths = set(ignored_paths or ())

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = _resolve_route_path(request)
        if path in self.ignored_paths:
            return await call_next(request)

        start_time = time.perf_counter()
        self.metrics.http_requests_in_progress.labels(service=self.metrics.service_name).inc()
        try:
            response = await call_next(request)
        except Exception:
            duration_seconds = time.perf_counter() - start_time
            self.metrics.record_request(
                method=request.method,
                path=_resolve_route_path(request),
                status_code=500,
                duration_seconds=duration_seconds,
            )
            raise
        finally:
            self.metrics.http_requests_in_progress.labels(service=self.metrics.service_name).dec()

        duration_seconds = time.perf_counter() - start_time
        self.metrics.record_request(
            method=request.method,
            path=_resolve_route_path(request),
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )
        return response


def install_prometheus(
    app: FastAPI,
    metrics: ServiceMetrics,
    *,
    metrics_path: str = "/metrics",
) -> None:
    """Attach Prometheus route and request middleware to a FastAPI app."""
    app.state.metrics = metrics

    @app.get(metrics_path, include_in_schema=False)
    async def metrics_endpoint() -> PlainTextResponse:
        return PlainTextResponse(
            content=metrics.render().decode("utf-8"),
            media_type=CONTENT_TYPE_LATEST,
        )

    app.add_middleware(
        PrometheusMetricsMiddleware,
        metrics=metrics,
        ignored_paths={metrics_path},
    )


def _resolve_route_path(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str):
        return route_path
    return request.url.path
