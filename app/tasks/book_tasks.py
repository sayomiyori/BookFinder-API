"""
Фоновые задачи для работы с книгами.

cleanup_stale_books — удаляет книги, к которым не обращались 30+ дней
                      и у которых нет записей в избранном.
                      Запускается автоматически каждую ночь через Celery Beat.
"""

import asyncio
import datetime
import logging

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.book_tasks.cleanup_stale_books",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def cleanup_stale_books(self) -> dict:
    """
    Синхронная обёртка над async-логикой для Celery.
    Удаляет устаревшие книги (last_accessed > 30 дней, без избранных).
    """
    try:
        return asyncio.run(_cleanup_async())
    except Exception as exc:
        logger.error("cleanup_stale_books failed: %s", exc)
        raise self.retry(exc=exc)


async def _cleanup_async() -> dict:
    """Async реализация очистки устаревших книг."""
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.config import get_settings
    from app.models.book import Book
    from app.models.favorite import Favorite

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

    async with async_session() as db:
        # Подзапрос: book_id-ы, которые есть в избранном хотя бы у одного пользователя
        favorited_ids = select(Favorite.book_id).distinct().scalar_subquery()

        stmt = (
            delete(Book)
            .where(Book.last_accessed < cutoff)
            .where(Book.id.not_in(favorited_ids))
        )
        result = await db.execute(stmt)
        await db.commit()
        count = result.rowcount

    await engine.dispose()
    logger.info("cleanup_stale_books: deleted %d stale books (cutoff=%s)", count, cutoff.date())
    return {"deleted": count, "cutoff": cutoff.isoformat()}
