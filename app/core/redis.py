"""
Async Redis клиент для кэширования запросов BookFinder API.
Соединение создаётся один раз при старте приложения и закрывается при остановке.
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Инициализирует соединение с Redis. Вызывается в lifespan."""
    global _redis_client
    settings = get_settings()
    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    # Ping для проверки доступности
    try:
        await _redis_client.ping()
        logger.info("Redis connected: %s", settings.redis_url)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — caching disabled", exc)
        _redis_client = None


async def close_redis() -> None:
    """Закрывает соединение с Redis. Вызывается при остановке приложения."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed.")


def get_redis_client() -> Optional[aioredis.Redis]:
    """Возвращает текущий Redis клиент (None если Redis недоступен)."""
    return _redis_client
