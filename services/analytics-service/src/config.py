"""Analytics Service settings."""

from functools import cached_property, lru_cache
from typing import Literal

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


class ClickHouseSettings(BaseSettings):
    """Shared ClickHouse settings."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="CLICKHOUSE_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "localhost"
    http_port: int = 8123
    user: str = "default"
    password: str = ""
    database: str = "analytics_db"


class Settings(BaseSettings):
    """Runtime configuration for Analytics Service."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="ANALYTICS_SERVICE_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "analytics-service"
    environment: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8007
    api_prefix: str = "/api/v1"

    kafka_enabled: bool = False
    consumer_group: str = "analytics-service-group"
    storage_backend: Literal["memory", "clickhouse"] = "memory"
    clickhouse_table: str = "analytics_events"
    clickhouse_timeout_seconds: float = 5.0

    @cached_property
    def kafka(self) -> KafkaSettings:
        """Get shared Kafka settings."""
        return KafkaSettings()

    @cached_property
    def clickhouse(self) -> ClickHouseSettings:
        """Get shared ClickHouse settings."""
        return ClickHouseSettings()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
