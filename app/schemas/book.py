"""Pydantic-схемы для книг (поиск и ответ API)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """Книга в ответе API."""

    id: int
    google_books_id: str
    title: str
    authors: list[str] | dict[str, Any] | None = None
    description: str | None = None
    published_date: str | None = None
    isbn: str | None = None
    page_count: int | None = None
    categories: list[str] | dict[str, Any] | None = None
    thumbnail: str | None = None
    language: str | None = None
    created_at: datetime
    last_accessed: datetime | None = None

    model_config = {"from_attributes": True}


class BookSearchResult(BaseModel):
    """Список книг с пагинацией."""

    items: list[BookResponse] = Field(default_factory=list, description="Список книг")
    total: int = Field(..., description="Оценка количества результатов")
    page: int = Field(..., ge=1, description="Текущая страница")
    limit: int = Field(..., ge=1, le=40, description="Размер страницы")
