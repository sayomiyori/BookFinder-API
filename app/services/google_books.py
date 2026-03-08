"""
Клиент Google Books API: поиск книг с обработкой ошибок и таймаутами.
"""

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Таймаут для запросов к API (секунды)
GOOGLE_BOOKS_TIMEOUT = 15.0


def _parse_volume(item: dict[str, Any]) -> dict[str, Any] | None:
    """
    Парсит один элемент из ответа Google Books API в структуру для модели Book.
    Возвращает None, если нет минимальных данных (id, title).
    """
    volume_id = item.get("id")
    info = item.get("volumeInfo") or {}
    title = info.get("title") or ""
    if not volume_id or not title:
        return None

    # ISBN из industryIdentifiers (тип ISBN_13 или ISBN_10)
    isbn = None
    for ident in info.get("industryIdentifiers") or []:
        if ident.get("type") in ("ISBN_13", "ISBN_10"):
            isbn = ident.get("identifier")
            break

    # Обложка
    image_links = info.get("imageLinks") or {}
    thumbnail = image_links.get("thumbnail") or image_links.get("smallThumbnail")

    # Язык
    lang = None
    if info.get("language"):
        lang = info["language"]

    return {
        "google_books_id": volume_id,
        "title": title[:1024],
        "authors": info.get("authors"),  # list[str] | None
        "description": (info.get("description") or "")[:10000],
        "published_date": (info.get("publishedDate") or "")[:32],
        "isbn": (isbn or "")[:32] or None,
        "page_count": info.get("pageCount"),
        "categories": info.get("categories"),  # list[str] | None
        "thumbnail": (thumbnail or "")[:2048] or None,
        "language": (lang or "")[:16] or None,
    }


async def fetch_books_from_google(query: str, max_results: int = 40) -> list[dict[str, Any]]:
    """
    Запрос к Google Books API. При ошибке или таймауте возвращает пустой список.
    """
    settings = get_settings()
    url = f"{settings.google_books_api_base.rstrip('/')}/volumes"
    params = {"q": query, "maxResults": min(max_results, 40)}

    try:
        async with httpx.AsyncClient(timeout=GOOGLE_BOOKS_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
    except httpx.TimeoutException:
        logger.warning("Google Books API timeout for q=%s", query)
        return []
    except httpx.HTTPStatusError as e:
        logger.warning("Google Books API error: %s %s", e.response.status_code, e.response.text[:200])
        return []
    except Exception as e:
        logger.exception("Google Books API request failed: %s", e)
        return []

    data = response.json()
    items = data.get("items") or []
    result = []
    for item in items:
        parsed = _parse_volume(item)
        if parsed:
            result.append(parsed)
    return result
