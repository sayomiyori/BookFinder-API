"""
Celery приложение BookFinder API.

Запуск воркера:
    celery -A app.worker worker --loglevel=info

Запуск планировщика (Beat):
    celery -A app.worker beat --loglevel=info

Запуск воркера + beat вместе (только для разработки):
    celery -A app.worker worker --beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bookfinder",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.book_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Автоматически удалять результаты задач через 1 час
    result_expires=3600,
    # Ограничение на число одновременных задач одного типа
    task_default_rate_limit="100/m",
    # Периодические задачи (Celery Beat)
    beat_schedule={
        "cleanup-stale-books-daily": {
            "task": "app.tasks.book_tasks.cleanup_stale_books",
            # Каждый день в 03:00 UTC
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
