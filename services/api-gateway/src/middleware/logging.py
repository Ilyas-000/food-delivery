"""Centralized request/response logging middleware."""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from shared.observability.request_context import CORRELATION_ID_HEADER, REQUEST_ID_HEADER
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.utils.ip import get_client_ip


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and outgoing responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request and log."""
        logger = structlog.get_logger()

        request_id = getattr(request.state, "request_id", None)
        if request_id is None:
            request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        request.state.request_id = request_id
        correlation_id = getattr(request.state, "correlation_id", request_id)
        request.state.correlation_id = correlation_id

        log_context = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": get_client_ip(request),
        }

        start_time = time.time()
        logger.info("Incoming request", **log_context)

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            logger.info(
                "Outgoing response",
                **log_context,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response

        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "Request failed",
                **log_context,
                duration_ms=duration_ms,
                error=str(exc),
                exc_info=settings.debug,
            )
            raise
