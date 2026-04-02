"""Payment domain exceptions."""


class PaymentError(Exception):
    """Base exception for payment domain errors."""


class PaymentNotFoundError(PaymentError):
    """Raised when payment does not exist."""


class PaymentStateTransitionError(PaymentError):
    """Raised when payment transition is not allowed."""


class PaymentIdempotencyConflictError(PaymentError):
    """Raised when idempotency key is reused with different payload."""


class PaymentValidationError(PaymentError):
    """Raised when payment request data is invalid."""
