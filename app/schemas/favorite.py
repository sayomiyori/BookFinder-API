"""Pydantic-схемы для избранного."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.book import BookResponse


class FavoriteItem(BaseModel):
    """Элемент избранного: книга и дата добавления."""

    book: BookResponse
    added_at: datetime

    model_config = {"from_attributes": False}


class FavoritesList(BaseModel):
    """Список избранных книг с пагинацией."""

    items: list[FavoriteItem] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=40)
