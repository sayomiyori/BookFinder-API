"""
Эндпоинты избранного: список, добавить, удалить.
Все запросы требуют JWT.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.book import BookResponse
from app.schemas.favorite import FavoriteItem, FavoritesList
from app.utils.dependencies import get_current_user, get_db

router = APIRouter()


@router.get("/me/favorites", response_model=FavoritesList)
async def list_favorites(
    page: Annotated[int, Query(ge=1, description="Страница")] = 1,
    limit: Annotated[int, Query(ge=1, le=40, description="Размер страницы")] = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoritesList:
    """Список избранных книг текущего пользователя с пагинацией."""
    # Общее количество
    count_stmt = select(func.count()).select_from(Favorite).where(Favorite.user_id == current_user.id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Страница записей с загрузкой книги
    offset = (page - 1) * limit
    stmt = (
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.added_at.desc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(Favorite.book))
    )
    result = await db.execute(stmt)
    favorites = result.scalars().all()

    items = [
        FavoriteItem(book=BookResponse.model_validate(fav.book), added_at=fav.added_at)
        for fav in favorites
    ]
    return FavoritesList(items=items, total=total, page=page, limit=limit)


@router.post("/me/favorites/{book_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Добавить книгу в избранное."""
    # Книга должна существовать
    book_result = await db.execute(select(Book).where(Book.id == book_id))
    if book_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    # Уже в избранном?
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.book_id == book_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Книга уже в избранном",
        )
    fav = Favorite(user_id=current_user.id, book_id=book_id)
    db.add(fav)
    await db.flush()
    return {"message": "Книга добавлена в избранное", "book_id": book_id}


@router.delete("/me/favorites/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Удалить книгу из избранного."""
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.book_id == book_id,
        )
    )
    fav = result.scalar_one_or_none()
    if fav is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена в избранном",
        )
    await db.delete(fav)
    await db.flush()
