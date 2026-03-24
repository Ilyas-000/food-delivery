"""Payment Service settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Payment Service."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="PAYMENT_SERVICE_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "payment-service"
    environment: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8004
    api_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
