class SharedError(Exception):
    """Base class for shared exceptions across services."""


class ValidationError(SharedError):
    """Raised when input validation fails."""


class NotFoundError(SharedError):
    """Raised when a requested resource is missing."""


class ConflictError(SharedError):
    """Raised when a resource conflict occurs."""


class UnauthorizedError(SharedError):
    """Raised when authentication fails."""


class ForbiddenError(SharedError):
    """Raised when access is denied."""


class ServiceUnavailableError(SharedError):
    """Raised when a dependency is unavailable."""
