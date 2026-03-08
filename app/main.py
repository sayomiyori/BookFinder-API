"""
Точка входа FastAPI приложения BookFinder API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом: запуск и остановка."""
    # Startup
    logger.info("BookFinder API starting...")
    yield
    # Shutdown
    logger.info("BookFinder API shutting down.")


def create_application() -> FastAPI:
    """Фабрика приложения FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="RESTful API для поиска книг с кешированием и избранным.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роутеры (подключим на следующих шагах)
    # from app.api.v1 import auth, books, favorites
    # app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    # app.include_router(books.router, prefix="/api/v1/books", tags=["books"])
    # app.include_router(favorites.router, prefix="/api/v1/users", tags=["favorites"])

    @app.get("/health", tags=["health"])
    async def health_check():
        """Проверка доступности сервиса."""
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_application()
