"""
Address Value Object.

Immutable address with coordinates for delivery radius calculation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    """
    Address value object.

    Business rules:
    - Street is required (2-200 characters)
    - City is required (2-100 characters)
    - Postal code is required (5-20 characters)
    - Coordinates are optional (for future delivery radius feature)
    - Immutable (frozen dataclass)

    Examples:
        >>> address = Address(
        ...     street="123 Main St",
        ...     city="Moscow",
        ...     postal_code="101000",
        ...     latitude=55.7558,
        ...     longitude=37.6173
        ... )
        >>> str(address)
        '123 Main St, Moscow, 101000'
    """

    street: str
    city: str
    postal_code: str
    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self) -> None:
        """Validate address after initialization."""
        # Validate street
        if not self.street or len(self.street) < 2:
            raise ValueError("Street must be at least 2 characters")
        if len(self.street) > 200:
            raise ValueError("Street must be at most 200 characters")

        # Validate city
        if not self.city or len(self.city) < 2:
            raise ValueError("City must be at least 2 characters")
        if len(self.city) > 100:
            raise ValueError("City must be at most 100 characters")

        # Validate postal code
        if not self.postal_code or len(self.postal_code) < 5:
            raise ValueError("Postal code must be at least 5 characters")
        if len(self.postal_code) > 20:
            raise ValueError("Postal code must be at most 20 characters")

        # Validate coordinates (if provided)
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")

        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")

        # Both coordinates must be provided or both must be None
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude must be provided or both must be None")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.street}, {self.city}, {self.postal_code}"

    @property
    def has_coordinates(self) -> bool:
        """Check if address has geographic coordinates."""
        return self.latitude is not None and self.longitude is not None

    @property
    def full_address(self) -> str:
        """Full address including coordinates if available."""
        base = str(self)
        if self.has_coordinates:
            return f"{base} (lat: {self.latitude}, lon: {self.longitude})"
        return base
