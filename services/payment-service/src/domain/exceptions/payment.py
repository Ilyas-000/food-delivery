"""Payment domain exceptions."""


class PaymentError(Exception):
    """Base exception for payment domain errors."""


class PaymentReservationNotFoundError(PaymentError):
    """Raised when reservation does not exist."""
