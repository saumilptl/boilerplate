"""Application configuration with Pydantic settings and EJSON secrets support."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from constants import Environment
from scripts.secrets.secret_loader import SecretsLoader


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE__")

    HOST: str = Field(..., description="Database host")
    PORT: int = Field(..., description="Database port")
    USER: str = Field(..., description="Database user")
    PASSWORD: str = Field(..., description="Database password")
    NAME: str = Field(..., description="Database name")
    DRIVER: str = Field(..., description="SQLAlchemy driver")
    SSL_MODE: str = Field(..., description="SSL mode (disable, allow, prefer, require, verify-ca, verify-full)")
    POOL_SIZE: int = Field(..., description="Connection pool size")
    MAX_OVERFLOW: int = Field(..., description="Max overflow connections")
    POOL_RECYCLE: int = Field(..., description="Pool recycle time in seconds")
    POOL_PRE_PING: bool = Field(..., description="Enable pool pre-ping")
    ECHO: bool = Field(..., description="Echo SQL queries")

    @property
    def url(self) -> str:
        """Get database URL."""
        return f"{self.DRIVER}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    @property
    def sync_url(self) -> str:
        """Get synchronous database URL for Alembic."""
        driver = self.DRIVER.replace("+asyncpg", "")
        return f"{driver}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


class RedisConfig(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS__")

    HOST: str = Field(..., description="Redis host")
    PORT: int = Field(..., description="Redis port")
    DB: int = Field(..., description="Redis database number")
    PASSWORD: str | None = Field(default=None, description="Redis password")
    SSL_MODE: bool = Field(..., description="Enable SSL")
    MAX_CONNECTIONS: int = Field(..., description="Max connections in pool")

    @property
    def url(self) -> str:
        """Get Redis URL."""
        protocol = "rediss" if self.SSL_MODE else "redis"
        auth = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"{protocol}://{auth}{self.HOST}:{self.PORT}/{self.DB}"


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration."""

    model_config = SettingsConfigDict(env_prefix="MONITORING__")

    # Datadog
    DD_ENABLED: bool = Field(default=False, description="Enable Datadog")
    DD_API_KEY: str | None = Field(default=None, description="Datadog API key")
    DD_SITE: str = Field(default="datadoghq.com", description="Datadog site")
    DD_APM_ENABLED: bool = Field(default=True, description="Enable APM")
    DD_LOGS_ENABLED: bool = Field(default=True, description="Enable log collection")

    # OpenTelemetry
    OTEL_ENABLED: bool = Field(default=False, description="Enable OpenTelemetry")
    OTEL_ENDPOINT: str | None = Field(default=None, description="OTEL collector endpoint")
    OTEL_SAMPLING_RATE: float = Field(default=0.1, description="Trace sampling rate (0.0-1.0)")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Log level")
    LOG_JSON: bool = Field(default=False, description="Output logs in JSON format")


class SecurityConfig(BaseSettings):
    """Security configuration."""

    model_config = SettingsConfigDict(env_prefix="SECURITY__")

    # JWT
    JWT_SECRET_KEY: str = Field(..., description="JWT signing key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration")

    # Password
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Require uppercase letter")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="Require lowercase letter")
    PASSWORD_REQUIRE_DIGIT: bool = Field(default=True, description="Require digit")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, description="Require special character")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Max requests per minute")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"], description="Allowed CORS origins")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials")


class WorkerConfig(BaseSettings):
    """Celery worker configuration."""

    model_config = SettingsConfigDict(env_prefix="WORKER__")

    TASK_RETRY_MAX_ATTEMPTS: int = Field(default=3, description="Max retry attempts")
    TASK_RETRY_BACKOFF: int = Field(default=5, description="Retry backoff in seconds")
    TASK_SOFT_TIME_LIMIT: int = Field(default=300, description="Soft time limit in seconds")
    TASK_TIME_LIMIT: int = Field(default=600, description="Hard time limit in seconds")
    WORKER_PREFETCH_MULTIPLIER: int = Field(default=1, description="Prefetch multiplier")
    WORKER_MAX_TASKS_PER_CHILD: int = Field(default=100, description="Max tasks per child process")
    WORKER_AUTOSCALE_MIN: int = Field(default=2, description="Min autoscale workers")
    WORKER_AUTOSCALE_MAX: int = Field(default=10, description="Max autoscale workers")
    ENABLE_BEAT: bool = Field(default=False, description="Enable Celery Beat scheduler")


class Config(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",  # Ignore extra fields from ENV_ prefixed vars
    )

    # Environment
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
    )
    SERVICE_NAME: str = Field(
        default="backend-api",
        description="Service name for monitoring",
    )
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")  # nosec B104
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of workers")
    RELOAD: bool = Field(default=False, description="Enable auto-reload")

    # Nested configurations
    DATABASE: DatabaseConfig
    REDIS: RedisConfig
    MONITORING: MonitoringConfig
    SECURITY: SecurityConfig
    WORKER: WorkerConfig


@lru_cache(maxsize=1)
def get_config(force_reload: bool = False) -> Config:
    """
    Get cached configuration instance.

    Loads from EJSON files with prefixes stripped.
    Environment variables can override secrets when force=False.

    Args:
        force_reload: Force reload of configuration

    Returns:
        Config instance with loaded secrets
    """
    if force_reload:
        get_config.cache_clear()

    environment_str = os.getenv("ENVIRONMENT", "development")
    environment = Environment(environment_str.lower())

    # Load secrets from EJSON (force=False allows env var overrides)
    secrets_loader = SecretsLoader(env=environment, force=False)
    secrets = secrets_loader.load_ejson_secrets()

    return Config(**secrets)


# Global config instance - lazy loaded to avoid import-time initialization
_config: Config | None = None


def config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = get_config()
    return _config
