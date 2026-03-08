"""
Конфигурация приложения через переменные окружения.
Используется pydantic-settings для валидации и загрузки из .env.
"""

from functools import lru_cache
from typing import List

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
    debug: bool = False

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # База данных
    database_url: str = "sqlite+aiosqlite:///./bookfinder.db"

    # Внешние API
    google_books_api_base: str = "https://www.googleapis.com/books/v1"
    google_vision_api_key: str | None = None
    google_gemini_api_key: str | None = None

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
