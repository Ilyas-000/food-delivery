"""Request correlation and request-level logging middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Populate request/correlation ids and emit consistent request logs."""

    def __init__(
        self,
        app: FastAPI,
        service_name: str,
        *,
        log_requests: bool = True,
    ) -> None:
        super().__init__(app)
        self.service_name = service_name
        self.log_requests = log_requests

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        correlation_id = request.headers.get(CORRELATION_ID_HEADER, request_id)

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            service=self.service_name,
            request_id=request_id,
            correlation_id=correlation_id,
        )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            if self.log_requests:
                self._log_request(
                    request=request,
                    status_code=500,
                    duration_ms=(time.perf_counter() - start_time) * 1000,
                    error=str(exc),
                    level="error",
                )
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        if self.log_requests:
            self._log_request(
                request=request,
                status_code=response.status_code,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                level="info",
            )

        structlog.contextvars.clear_contextvars()
        return response

    def _log_request(
        self,
        *,
        request: Request,
        status_code: int,
        duration_ms: float,
        level: str,
        error: str | None = None,
    ) -> None:
        logger = structlog.get_logger()
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        payload = {
            "service": self.service_name,
            "method": request.method,
            "path": route_path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "request_id": request.state.request_id,
            "correlation_id": request.state.correlation_id,
        }
        if error is not None:
            payload["error"] = error

        log_method = getattr(logger, level)
        log_method("http.request", **payload)


def install_request_context(
    app: FastAPI,
    *,
    service_name: str,
    log_requests: bool = True,
) -> None:
    """Attach request context middleware to a FastAPI app."""
    app.add_middleware(
        RequestContextMiddleware,
        service_name=service_name,
        log_requests=log_requests,
    )
