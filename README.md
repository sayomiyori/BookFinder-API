# BookFinder API

![CI](https://github.com/sayomiyori/BookFinder-API/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/sayomiyori/BookFinder-API/actions/workflows/cd.yml/badge.svg)
![Coverage](https://codecov.io/gh/sayomiyori/BookFinder-API/graph/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)
![Docker](https://img.shields.io/badge/docker-multistage-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Production-grade REST API for book search with Google Books integration, Redis caching, JWT authentication, and Celery background tasks.
Built with FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, and Redis.

---

## Architecture

```
Client
  │
  ▼
FastAPI (Docker multi-stage)
  ├── Rate Limiting (slowapi)        ← 5–200 req/min per endpoint
  ├── /api/v1/auth                   ← JWT register / login
  ├── /api/v1/books ──► Redis Cache  ← 5 min TTL on search results
  │         └────────► Google Books API + PostgreSQL
  ├── /api/v1/users/me/favorites     ← paginated, JWT-protected
  ├── /health                        ← Railway liveness probe
  └── /metrics                       ← Prometheus scrape endpoint
  │
  ▼
Background (Celery + Redis Broker)
  └── cleanup_stale_books            ← daily at 03:00 UTC
  │
  ▼
Observability
  ├── Sentry                         ← error tracking (optional)
  └── Prometheus + Grafana           ← metrics (optional)
  │
  ▼
GitHub Actions CI/CD
  ├── ruff lint + pytest + Codecov
  └── Docker build → GHCR → Railway auto-deploy
```

---

## Tech Stack

| Layer             | Technology                              |
|-------------------|-----------------------------------------|
| Framework         | FastAPI 0.109+                          |
| ORM               | SQLAlchemy 2.0 (async) + Alembic        |
| Database          | PostgreSQL 16 (prod) / SQLite (dev)     |
| Cache             | Redis 7 + redis-py (async)              |
| Background Tasks  | Celery 5 + Celery Beat                  |
| Auth              | JWT HS256 (python-jose) + bcrypt        |
| Rate Limiting     | slowapi (per-endpoint limits)           |
| Error Monitoring  | Sentry SDK (FastAPI + SQLAlchemy)       |
| Metrics           | Prometheus client + Grafana             |
| External API      | Google Books API                        |
| CI/CD             | GitHub Actions → GHCR → Railway        |
| Container         | Docker multi-stage + Docker Compose     |

---

## API Endpoints

### Auth `/api/v1/auth`

| Method | Path          | Rate Limit  | Auth | Description               |
|--------|---------------|-------------|------|---------------------------|
| POST   | `/register`   | 5/min       | —    | Register, returns JWT     |
| POST   | `/login`      | 10/min      | —    | Login (JSON body)         |
| POST   | `/login/form` | 10/min      | —    | Login (form, for Swagger) |
| GET    | `/me`         | —           | JWT  | Current user profile      |

### Books `/api/v1/books`

| Method | Path         | Rate Limit  | Auth | Description                              |
|--------|--------------|-------------|------|------------------------------------------|
| GET    | `?q=&page=&limit=` | 30/min | —  | Hybrid search: DB + Google Books, cached |
| GET    | `/{book_id}` | —           | —    | Get book by ID, cached 10 min            |
| POST   | `/`          | —           | JWT  | Manually add a book                      |

**Search** supports pagination: `?q=python&page=2&limit=20`
Results cached in Redis for **5 minutes**. Automatically fetches from Google Books when local DB has fewer results than `limit`.

### Favorites `/api/v1/users`

| Method | Path                      | Auth | Description                |
|--------|---------------------------|------|----------------------------|
| GET    | `/me/favorites?page=&limit=` | JWT | Paginated favorites list |
| POST   | `/me/favorites/{book_id}` | JWT  | Add book to favorites      |
| DELETE | `/me/favorites/{book_id}` | JWT  | Remove from favorites      |

### System

| Method | Path       | Description                      |
|--------|------------|----------------------------------|
| GET    | `/health`  | Liveness probe (Railway checks)  |
| GET    | `/metrics` | Prometheus metrics               |
| GET    | `/docs`    | Swagger UI (OpenAPI 3.1)         |
| GET    | `/redoc`   | ReDoc                            |

---

## Deploy on Railway

1. **New Project → Deploy from GitHub repo** — выбери `BookFinder-API`
2. Добавь **PostgreSQL plugin** → `DATABASE_URL` подставится автоматически
3. Добавь **Redis plugin** → `REDIS_URL` подставится автоматически
4. В **Variables** добавь вручную:

```
SECRET_KEY=<openssl rand -hex 32>
CORS_ORIGINS=*
```

5. Railway сам сбилдит Dockerfile и задеплоит — `railway.toml` в корне управляет параметрами.

> Railway автоматически деплоит при каждом push в `main`. Healthcheck на `/health` подтверждает успешный деплой.

---

## Local Development

```bash
# 1. Клонировать и настроить окружение
git clone https://github.com/sayomiyori/BookFinder-API.git
cd BookFinder-API
cp .env.example .env        # заполни SECRET_KEY

# 2. Запустить всё (API + PostgreSQL + Redis + Celery)
docker compose up -d --build

# 3. Применить миграции (если запускаешь без Docker)
alembic upgrade head

# 4. Эндпоинты
# Swagger UI:  http://localhost:8001/docs
# Metrics:     http://localhost:8001/metrics
# Health:      http://localhost:8001/health
```

**С мониторингом (Prometheus + Grafana):**
```bash
docker compose -f docker-compose.monitoring.yml up -d
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000  (admin / admin)
```

---

## Environment Variables

| Variable                       | Default                        | Description                              |
|-------------------------------|--------------------------------|------------------------------------------|
| `SECRET_KEY`                  | `change-me-in-production`      | JWT signing key — **обязательно сменить**|
| `DATABASE_URL`                | `sqlite+aiosqlite:///./...`    | Async DB URL; Railway подставит сам      |
| `REDIS_URL`                   | `redis://localhost:6379/0`     | Redis URL; без Redis кэш отключается     |
| `CELERY_BROKER_URL`           | `redis://localhost:6379/1`     | Celery broker                            |
| `CELERY_RESULT_BACKEND`       | `redis://localhost:6379/2`     | Celery result backend                    |
| `SENTRY_DSN`                  | —                              | Sentry DSN (опционально)                 |
| `SENTRY_ENVIRONMENT`          | `production`                   | Sentry environment tag                   |
| `CORS_ORIGINS`                | `http://localhost:3000`        | Allowed origins через запятую или `*`    |
| `RATE_LIMIT_ENABLED`          | `true`                         | `false` отключает лимиты (CI/тесты)      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                           | JWT TTL в минутах                        |
| `DEBUG`                       | `false`                        | SQL echo logging                         |

---

## Background Tasks (Celery)

Запуск воркера отдельно (или через `docker compose up celery-worker`):

```bash
celery -A app.worker worker --loglevel=info
celery -A app.worker beat   --loglevel=info   # планировщик
```

| Task                  | Schedule         | Description                                    |
|-----------------------|------------------|------------------------------------------------|
| `cleanup_stale_books` | Ежедневно 03:00  | Удаляет книги без доступа 30+ дней, не в избранном |

---

## CI/CD

Каждый push запускает:

1. **Lint** — `ruff check .`
2. **Tests** — `pytest` с SQLite in-memory, отчёт в Codecov
3. На merge в `main`: Docker image → GHCR → Railway auto-deploy

Без ручных деплоев. Зелёный бейдж = production актуален.

---

## Monitoring

Prometheus scrapes `/metrics` каждые 15s. Основные метрики:

```promql
rate(http_requests_total[1m])                                         # RPS
rate(http_errors_total[1m])                                           # Error rate
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))  # p95 latency
```

---

## Project Structure

```
app/
├── main.py                  # FastAPI app factory + lifespan
├── metrics.py               # Prometheus middleware + /metrics
├── worker.py                # Celery app + beat schedule
├── api/v1/
│   ├── auth.py              # Register, login, /me
│   ├── books.py             # Search (cached), get, create
│   └── favorites.py         # List, add, remove (paginated)
├── core/
│   ├── config.py            # pydantic-settings + DB URL normalizer
│   ├── cache.py             # Redis get/set/delete helpers
│   ├── database.py          # SQLAlchemy async engine
│   ├── limiter.py           # slowapi singleton (RATE_LIMIT_ENABLED)
│   ├── redis.py             # Redis lifespan init/close
│   └── security.py          # JWT + bcrypt
├── models/                  # SQLAlchemy ORM (User, Book, Favorite)
├── schemas/                 # Pydantic v2 schemas
├── services/
│   └── google_books.py      # Google Books API client
├── tasks/
│   └── book_tasks.py        # Celery task: cleanup_stale_books
└── tests/                   # pytest-asyncio, SQLite in-memory
alembic/                     # DB migrations
Dockerfile                   # Multi-stage build (builder + runtime)
docker-compose.yml           # Local dev stack
railway.toml                 # Railway deployment config
CHANGELOG.md                 # Semantic versioning history
```

---

## License

MIT
