"""
Эндпоинты книг: поиск, детализация, ручное добавление.
"""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.schemas.book import BookCreate, BookResponse, BookSearchResult
from app.services.google_books import fetch_books_from_google
from app.utils.dependencies import get_current_user, get_db
from app.models.user import User

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


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
) -> Book:
    """Детальная информация о книге по id (из локальной БД)."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    return book


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Book:
    """
    Ручное добавление книги. Требуется авторизация (JWT).
    """
    result = await db.execute(select(Book).where(Book.google_books_id == data.google_books_id))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Книга с таким google_books_id уже существует",
        )
    book = Book(
        google_books_id=data.google_books_id,
        title=data.title,
        authors=data.authors,
        description=data.description,
        published_date=data.published_date,
        isbn=data.isbn,
        page_count=data.page_count,
        categories=data.categories,
        thumbnail=data.thumbnail,
        language=data.language,
    )
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book
