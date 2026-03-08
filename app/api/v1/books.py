"""
Эндпоинты книг: поиск (БД + Google Books API с кешированием).
"""

import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.models.book import Book
from app.schemas.book import BookResponse, BookSearchResult
from app.services.google_books import fetch_books_from_google
from app.utils.dependencies import get_db

router = APIRouter()


def _search_condition(q: str):
    """Условие поиска по title, isbn, description (подходит для SQLite и PostgreSQL)."""
    p = f"%{q}%"
    return or_(
        Book.title.like(p),
        Book.isbn.like(p),
        Book.description.like(p),
    )


@router.get("", response_model=BookSearchResult)
async def search_books(
    q: Annotated[str, Query(min_length=1, description="Поисковый запрос")],
    page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    limit: Annotated[int, Query(ge=1, le=40, description="Размер страницы")] = 20,
    db: AsyncSession = Depends(get_db),
) -> BookSearchResult:
    """
    Поиск книг. Сначала ищем в локальной БД, при нехватке результатов — запрос к Google Books API,
    новые книги сохраняются в БД. Возвращается объединённый результат с пагинацией.
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1) Подсчёт в БД и при нехватке — подтягивание из Google
    count_stmt = select(func.count()).select_from(Book).where(_search_condition(q))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 2) Если мало результатов — подтягиваем из Google и сохраняем в БД
    if total < limit:
        raw_books = await fetch_books_from_google(q, max_results=min(40, limit * 2))
        for data in raw_books:
            existing = await db.execute(select(Book).where(Book.google_books_id == data["google_books_id"]))
            book = existing.scalar_one_or_none()
            if book is None:
                db.add(
                    Book(
                        google_books_id=data["google_books_id"],
                        title=data["title"],
                        authors=data.get("authors"),
                        description=data.get("description") or None,
                        published_date=data.get("published_date") or None,
                        isbn=data.get("isbn"),
                        page_count=data.get("page_count"),
                        categories=data.get("categories"),
                        thumbnail=data.get("thumbnail"),
                        language=data.get("language"),
                        last_accessed=now,
                    )
                )
            else:
                book.last_accessed = now
        await db.flush()

        # Пересчитываем total после добавления
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

    # 3) Выдача страницы из БД
    offset = (page - 1) * limit
    stmt = (
        select(Book)
        .where(_search_condition(q))
        .order_by(Book.last_accessed.desc().nulls_last(), Book.id.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    books = result.scalars().all()

    return BookSearchResult(
        items=[BookResponse.model_validate(b) for b in books],
        total=total,
        page=page,
        limit=limit,
    )
