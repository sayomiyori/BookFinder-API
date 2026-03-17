# Changelog

All notable changes to **BookFinder API** are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

---

## [1.0.0] — 2026-03-17

Production-grade upgrade: Redis caching, Celery workers, Sentry monitoring,
rate limiting, multi-stage Docker, enhanced OpenAPI docs.

### Added

#### Redis Caching
- `app/core/redis.py` — async Redis client (`redis.asyncio`) с graceful degradation:
  если Redis недоступен, API продолжает работать без кэша
- `app/core/cache.py` — утилиты `cache_get` / `cache_set` / `cache_delete`
- Результаты поиска книг кэшируются на **5 минут** (ключ `books:search:{q}:{page}:{limit}`)
- Детали книги кэшируются на **10 минут** (ключ `books:detail:{id}`)

#### Celery (Background Tasks)
- `app/worker.py` — Celery app с Redis как брокером и бэкендом результатов
- `app/tasks/book_tasks.py` — задача `cleanup_stale_books`: удаляет книги без
  избранных, к которым не обращались 30+ дней; запускается ежедневно в 03:00 UTC
- Celery Beat для расписания периодических задач

#### Sentry Error Monitoring
- Интеграция `sentry-sdk[fastapi]` в `app/main.py`
- Автоматическая трассировка FastAPI-запросов и SQLAlchemy-запросов
- Настройка через `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`
- Не активируется, если `SENTRY_DSN` не задан (dev-режим)

#### Rate Limiting (slowapi)
- `app/core/limiter.py` — singleton `Limiter` с `get_remote_address`
- `POST /api/v1/auth/register` — **5 req/min**
- `POST /api/v1/auth/login`, `/login/form` — **10 req/min**
- `GET /api/v1/books` (search) — **30 req/min**
- Default limit для всех остальных роутов — **200 req/min**
- HTTP 429 с `Retry-After` заголовком при превышении

#### OpenAPI Documentation
- Расширенное описание API с markdown (возможности, схема авторизации)
- `openapi_tags` с описанием каждого тэга (`auth`, `books`, `favorites`, `health`)
- `contact` и `license_info` в метаданных OpenAPI
- `summary` и `responses` на каждом эндпоинте

#### Docker (Multi-stage Build)
- `Dockerfile` переписан с **двухстадийной сборкой**:
  - `builder` stage: gcc + libpq-dev, установка зависимостей в `/install`
  - `runtime` stage: только `libpq5`, без build-инструментов
- Запуск от непривилегированного пользователя `appuser`
- `PYTHONDONTWRITEBYTECODE=1` для экономии места

#### CI/CD Updates
- `.github/workflows/cd.yml`: Docker Buildx + GitHub Actions layer cache (`type=gha`)

#### Configuration
- `app/core/config.py` — новые поля: `app_version`, `redis_url`,
  `celery_broker_url`, `celery_result_backend`, `sentry_dsn`,
  `sentry_environment`, `sentry_traces_sample_rate`, `rate_limit_enabled`
- `.env.example` обновлён со всеми новыми переменными и комментариями

#### docker-compose.yml Updates
- Добавлены сервисы: `redis`, `celery-worker`, `celery-beat`
- `redis_data` volume для персистентности

### Changed
- `app/main.py`: lifespan теперь инициализирует/закрывает Redis-соединение
- `app/api/v1/books.py`: `search_books` и `get_book` используют Redis-кэш
- `app/api/v1/auth.py`: все `POST`-эндпоинты получили `@limiter.limit(...)`
- `requirements.txt`: добавлены `redis[hiredis]`, `celery[redis]`,
  `sentry-sdk[fastapi]`, `slowapi`

---

## [0.1.0] — 2025-12-01

Initial release.

### Added
- FastAPI приложение с async SQLAlchemy 2.0 (PostgreSQL + SQLite)
- JWT аутентификация (register, login, /me)
- Поиск книг с гибридной стратегией (локальная БД + Google Books API)
- Пагинация в поиске и избранном
- Управление избранным (CRUD)
- Alembic миграции (`users`, `books`, `favorites`)
- Prometheus метрики (`/metrics`): request count, latency, errors
- Docker Compose (app + PostgreSQL)
- `docker-compose.monitoring.yml` (Prometheus + Grafana)
- GitHub Actions CI: lint (ruff), pytest с coverage, Codecov
- GitHub Actions CD: сборка и пуш Docker-образа в GHCR

[Unreleased]: https://github.com/sayomiyori/BookFinder-API/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sayomiyori/BookFinder-API/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/sayomiyori/BookFinder-API/releases/tag/v0.1.0
