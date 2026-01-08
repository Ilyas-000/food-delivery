"""
Shared base exceptions.

Note: Most exceptions should be service-specific!
Only truly common exceptions belong here (HTTP-like errors for inter-service communication).

Import explicitly:
    from shared.exceptions.base import NotFoundError, ConflictError
"""
