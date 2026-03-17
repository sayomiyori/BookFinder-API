"""
Утилиты кэширования: get / set / delete с graceful degradation.
При недоступном Redis операции молча пропускаются — API продолжает работать.
"""

import json
import logging
from typing import Any, Optional

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

# TTL (секунды)
SEARCH_TTL = 300       # 5 минут
BOOK_DETAIL_TTL = 600  # 10 минут


def search_cache_key(q: str, page: int, limit: int) -> str:
    return f"books:search:{q.lower()}:{page}:{limit}"


def book_detail_cache_key(book_id: int) -> str:
    return f"books:detail:{book_id}"


async def cache_get(key: str) -> Optional[Any]:
    """
    Получить значение из кэша по ключу.
    Возвращает десериализованный объект или None при промахе / ошибке.
    """
    redis = get_redis_client()
    if redis is None:
        return None
    try:
        value = await redis.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:
        logger.warning("Cache GET error [%s]: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """
    Записать значение в кэш с TTL (секунды).
    При ошибке Redis предупреждение логируется, исключение не пробрасывается.
    """
    redis = get_redis_client()
    if redis is None:
        return
    try:
        await redis.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
    except Exception as exc:
        logger.warning("Cache SET error [%s]: %s", key, exc)


async def cache_delete(key: str) -> None:
    """Удалить ключ из кэша."""
    redis = get_redis_client()
    if redis is None:
        return
    try:
        await redis.delete(key)
    except Exception as exc:
        logger.warning("Cache DELETE error [%s]: %s", key, exc)
