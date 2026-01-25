"""IP address helpers (ProxyHeadersMiddleware adjusts request.client)."""

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Return client IP from ASGI scope (set by ProxyHeadersMiddleware if enabled)."""
    return request.client.host if request.client else "unknown"
