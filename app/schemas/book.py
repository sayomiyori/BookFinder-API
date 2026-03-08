"""Pydantic-схемы для книг (поиск, создание и ответ API)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    """Тело запроса для ручного добавления книги."""

    google_books_id: str = Field(..., min_length=1, max_length=64, description="Уникальный ID (например из Google Books или свой)")
    title: str = Field(..., min_length=1, max_length=1024)
    authors: list[str] | None = None
    description: str | None = None
    published_date: str | None = Field(None, max_length=32)
    isbn: str | None = Field(None, max_length=32)
    page_count: int | None = None
    categories: list[str] | None = None
    thumbnail: str | None = Field(None, max_length=2048)
    language: str | None = Field(None, max_length=16)


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
