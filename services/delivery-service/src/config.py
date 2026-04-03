"""Delivery Service settings."""

from functools import cached_property, lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    """Shared Kafka settings."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="KAFKA_",
        case_sensitive=False,
        extra="ignore",
    )

    bootstrap_servers: str = "localhost:9093"


class Settings(BaseSettings):
    """Runtime configuration for Delivery Service."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="DELIVERY_SERVICE_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "delivery-service"
    environment: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8005
    api_prefix: str = "/api/v1"

    realtime_backend: str = "memory"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 2
    redis_password: str | None = None
    redis_channel_prefix: str = "delivery"
    kafka_enabled: bool = False

    @cached_property
    def kafka(self) -> KafkaSettings:
        """Get shared Kafka settings."""
        return KafkaSettings()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
