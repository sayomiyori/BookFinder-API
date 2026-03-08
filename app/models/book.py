"""Модель книги (кеш из Google Books + ручное добавление)."""

import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Book(Base):
    """
    Книга: данные из Google Books API или ручной ввод.
    google_books_id уникален; last_accessed для очистки кеша.
    """

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    google_books_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    authors: Mapped[dict[str, Any] | list[str] | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    categories: Mapped[dict[str, Any] | list[str] | None] = mapped_column(JSON, nullable=True)
    thumbnail: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        nullable=False,
    )
    last_accessed: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite",
        back_populates="book",
        cascade="all, delete-orphan",
    )
