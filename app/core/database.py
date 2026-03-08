"""
Асинхронное подключение к БД: движок SQLAlchemy и фабрика сессий.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import Base  # noqa: F401 — импорт для регистрации моделей

settings = get_settings()

# Асинхронный движок. echo=SQL при DEBUG для отладки запросов.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Фабрика асинхронных сессий: автокоммит и автофлаш отключены (контроль в коде).
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: выдаёт сессию БД на запрос и закрывает по завершении."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
