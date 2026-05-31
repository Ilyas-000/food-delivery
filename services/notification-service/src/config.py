"""Notification Service settings."""

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
    consumer_auto_offset_reset: str = "earliest"


class Settings(BaseSettings):
    """Runtime configuration for Notification Service."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="NOTIFICATION_SERVICE_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "notification-service"
    environment: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8006
    api_prefix: str = "/api/v1"
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"

    kafka_enabled: bool = False
    consumer_group: str = "notification-service-group"
    mock_email_domain: str = "notifications.local"
    mock_push_prefix: str = "device"

    @cached_property
    def kafka(self) -> KafkaSettings:
        """Get shared Kafka settings."""
        return KafkaSettings()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
