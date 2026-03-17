"""
Конфигурация приложения через переменные окружения.
Используется pydantic-settings для валидации и загрузки из .env.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # игнорировать лишние переменные
    )

    # Приложение
    app_name: str = "BookFinder API"
    app_version: str = "1.0.0"
    debug: bool = False

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # База данных
    database_url: str = "sqlite+aiosqlite:///./bookfinder.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Нормализует DATABASE_URL для async-движка.

        Railway и Heroku отдают postgres:// или postgresql:// —
        приводим к postgresql+asyncpg://, который требует asyncpg.
        """
        if not isinstance(v, str):
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def database_url_sync(self) -> str:
        """URL для синхронного подключения (Alembic).

        Возвращает URL без async-драйвера: asyncpg → psycopg2 (стандарт).
        """
        url = self.database_url
        if url.startswith("sqlite+aiosqlite"):
            return url.replace("sqlite+aiosqlite", "sqlite", 1)
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "", 1)
        return url

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Sentry
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "production"
    sentry_traces_sample_rate: float = 0.1  # 10% трасс

    # Rate limiting
    rate_limit_enabled: bool = True

    # Внешние API
    google_books_api_base: str = "https://www.googleapis.com/books/v1"
    google_vision_api_key: Optional[str] = None
    google_gemini_api_key: Optional[str] = None

    # CORS — список origins через запятую в .env
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins как список строк."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Возвращает синглтон настроек (кэшируется)."""
    return Settings()
