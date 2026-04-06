"""Analytics domain exceptions."""


class AnalyticsError(Exception):
    """Base analytics exception."""


class AnalyticsValidationError(AnalyticsError):
    """Raised when analytics input is invalid."""
