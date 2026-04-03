"""Courier location value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """Geographic coordinates in WGS84."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
