"""API Gateway Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API Gateway settings."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="GATEWAY_",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"  # nosec B104
    port: int = 8000
    environment: str = "development"
    debug: bool = True
    version: str = "1.0.0"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # JWT secret (MUST match User Service for token validation)
    jwt_secret_key: str

    # Redis (for rate limiting)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1  # Different from User Service (db=0)
    redis_password: str | None = None
    redis_connect_retries: int = 30
    redis_connect_delay_seconds: float = 2.0

    # Service URLs (internal Docker network)
    user_service_url: str = "http://user-service:8001"
    restaurant_service_url: str = "http://restaurant-service:8002"
    order_service_url: str = "http://order-service:8003"
    payment_service_url: str = "http://payment-service:8004"
    delivery_service_url: str = "http://delivery-service:8005"
    analytics_service_url: str = "http://analytics-service:8007"
    review_service_url: str = "http://review-service:8008"

    # Proxy timeouts (seconds)
    proxy_timeout_default: float = 30.0
    proxy_timeout_auth: float = 15.0
    proxy_timeout_user: float = 10.0
    proxy_timeout_restaurant: float = 10.0
    proxy_timeout_order: float = 10.0
    proxy_timeout_payment: float = 10.0
    proxy_timeout_delivery: float = 10.0
    proxy_timeout_analytics: float = 10.0
    proxy_timeout_review: float = 10.0

    # Circuit Breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 30.0

    # Rate Limiting Configuration
    rate_limit_enabled: bool = True

    # Login rate limits (softened for better UX)
    login_per_ip_minute: int = 15  # was 10
    login_per_ip_hour: int = 100
    login_per_account_minute: int = 8  # was 5
    login_per_account_hour: int = 20
    login_per_ip_account_minute: int = 5  # was 3
    login_max_fails_count: int = 8  # was 5
    login_max_fails_window: int = 600  # 10 minutes
    login_cooldown_duration: int = 300  # 5 minutes (was 15)

    # Refresh rate limits
    refresh_per_jti_minute: int = 10
    refresh_per_jti_hour: int = 60
    refresh_per_user_minute: int = 30
    refresh_per_user_hour: int = 300
    refresh_per_ip_minute: int = 60
    refresh_per_ip_hour: int = 1000
    refresh_invalid_per_ip_minute: int = 5
    refresh_invalid_per_ip_hour: int = 20

    # Global auth rate limits
    auth_global_per_ip_minute: int = 60
    auth_global_burst: int = 20
    auth_global_per_ip_hour: int = 1000

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

    # Proxy headers
    trust_proxy_headers: bool = True
    trusted_proxy_ips: str = ""


settings = Settings()  # type: ignore[call-arg]
