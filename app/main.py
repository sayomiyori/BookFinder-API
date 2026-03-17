"""
Точка входа FastAPI приложения BookFinder API.
"""

import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.redis import close_redis, init_redis
from app.metrics import setup_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _init_sentry(settings) -> None:
    """Инициализирует Sentry SDK, если задан DSN."""
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not set — error monitoring disabled.")
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=f"bookfinder-api@{settings.app_version}",
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )
    logger.info("Sentry initialized (env=%s)", settings.sentry_environment)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом: запуск и остановка."""
    logger.info("BookFinder API starting...")
    await init_redis()
    yield
    await close_redis()
    logger.info("BookFinder API shutting down.")


# OpenAPI тэги с описаниями
TAGS_METADATA = [
    {
        "name": "auth",
        "description": (
            "Аутентификация и управление аккаунтом. "
            "Регистрация возвращает JWT; используйте его в заголовке "
            "`Authorization: Bearer <token>` для защищённых эндпоинтов."
        ),
    },
    {
        "name": "books",
        "description": (
            "Поиск и просмотр книг. "
            "Результаты кэшируются в Redis на 5 минут. "
            "При нехватке локальных данных автоматически запрашивает Google Books API."
        ),
    },
    {
        "name": "favorites",
        "description": "Управление списком избранных книг пользователя. Требует JWT.",
    },
    {
        "name": "health",
        "description": "Проверка работоспособности сервиса (liveness probe).",
    },
]

APP_DESCRIPTION = """
## BookFinder API

RESTful API для поиска книг с кешированием, аутентификацией и избранным.

### Возможности
- **Поиск книг** — гибридный поиск: локальная БД + Google Books API
- **Redis-кэш** — результаты поиска кэшируются на 5 минут
- **JWT авторизация** — регистрация / вход / получение профиля
- **Избранное** — сохранение книг с пагинацией
- **Rate Limiting** — защита от перегрузки (slowapi)
- **Метрики** — Prometheus endpoint `/metrics`
- **Фоновые задачи** — Celery + Redis (очистка устаревших книг)

### Авторизация
1. Зарегистрируйтесь через `POST /api/v1/auth/register`
2. Нажмите кнопку **Authorize** и введите `Bearer <access_token>`
"""


def create_application() -> FastAPI:
    """Фабрика приложения FastAPI."""
    settings = get_settings()

    _init_sentry(settings)

    app = FastAPI(
        title=settings.app_name,
        description=APP_DESCRIPTION,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        openapi_tags=TAGS_METADATA,
        contact={
            "name": "BookFinder API",
            "url": "https://github.com/sayomiyori/BookFinder-API",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    setup_metrics(app)

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роутеры
    from app.api.v1 import auth, books, favorites
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(books.router, prefix="/api/v1/books", tags=["books"])
    app.include_router(favorites.router, prefix="/api/v1/users", tags=["favorites"])

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    @app.get(
        "/health",
        tags=["health"],
        summary="Liveness probe",
        responses={200: {"description": "Сервис работает нормально"}},
    )
    async def health_check():
        """Проверка доступности сервиса."""
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    return app


app = create_application()
