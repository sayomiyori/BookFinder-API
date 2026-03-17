# BookFinder API

![CI](https://github.com/sayomiyori/BookFinder-API/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/sayomiyori/BookFinder-API/actions/workflows/cd.yml/badge.svg)
![Coverage](https://codecov.io/gh/sayomiyori/BookFinder-API/graph/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

REST API for book search with Google Books integration, favorites, and JWT authentication.
Built with FastAPI, SQLAlchemy 2.0 (async), and PostgreSQL.

## Architecture

```
Client
  |
  v
FastAPI (Docker)
  |-- JWT Auth (/api/v1/auth)
  |-- /api/v1/books  ->  Google Books API + PostgreSQL cache
  +-- /api/v1/fav   ->  PostgreSQL
  |
  v
GitHub Actions CI/CD
  |-- ruff lint
  |-- pytest (coverage 87%)
  +-- Docker -> GHCR -> Railway (prod)
  |
  v
Prometheus + Grafana (observability)
```

## Tech Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Framework     | FastAPI 0.109+                      |
| ORM           | SQLAlchemy 2.0 (async) + Alembic    |
| Database      | PostgreSQL 16 (prod) / SQLite (dev) |
| Auth          | JWT (python-jose) + bcrypt          |
| External API  | Google Books API                    |
| Metrics       | Prometheus + Grafana                |
| CI/CD         | GitHub Actions -> GHCR -> Railway   |
| Container     | Docker + Docker Compose             |

## API Endpoints

### Auth (`/api/v1/auth`)
| Method | Path           | Description              | Auth |
|--------|----------------|--------------------------|------|
| POST   | `/register`    | Register new user        | No   |
| POST   | `/login`       | Login (JSON)             | No   |
| POST   | `/login/form`  | Login (form, for Swagger)| No   |
| GET    | `/me`          | Current user info        | JWT  |

### Books (`/api/v1/books`)
| Method | Path           | Description                           | Auth |
|--------|----------------|---------------------------------------|------|
| GET    | `?q=...`       | Search books (DB + Google Books API)  | No   |
| GET    | `/{book_id}`   | Get book by ID                        | No   |
| POST   | `/`            | Add book manually                     | JWT  |

### Favorites (`/api/v1/users`)
| Method | Path                      | Description            | Auth |
|--------|---------------------------|------------------------|------|
| GET    | `/me/favorites`           | List user's favorites  | JWT  |
| POST   | `/me/favorites/{book_id}` | Add to favorites       | JWT  |
| DELETE | `/me/favorites/{book_id}` | Remove from favorites  | JWT  |

### System
| Method | Path       | Description         |
|--------|------------|---------------------|
| GET    | `/health`  | Health check        |
| GET    | `/metrics` | Prometheus metrics  |
| GET    | `/docs`    | Swagger UI          |
| GET    | `/redoc`   | ReDoc               |

## CI/CD

Every push triggers:
1. **Lint** -- ruff checks code style
2. **Tests** -- pytest with real PostgreSQL (not mocks)
3. **Coverage** -- reported to Codecov
4. On merge to `main`: Docker image -> GHCR -> Railway auto-deploy

No manual deploys. Green badge = production is up to date.

## Local Development

```bash
# Clone and configure
git clone https://github.com/sayomiyori/BookFinder-API.git
cd BookFinder-API
cp .env.example .env

# Start app + database
docker-compose up -d --build

# Start monitoring (optional)
docker-compose -f docker-compose.monitoring.yml up -d

# Endpoints
# API:        http://localhost:8001/docs
# Metrics:    http://localhost:8001/metrics
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
```

## Environment Variables

| Variable                     | Default                  | Description                |
|------------------------------|--------------------------|----------------------------|
| `SECRET_KEY`                 | `change-me-in-production`| JWT signing key            |
| `DATABASE_URL`               | `sqlite+aiosqlite://...` | Async database URL         |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `30`                     | JWT token TTL              |
| `CORS_ORIGINS`               | `http://localhost:3000`  | Allowed origins (CSV)      |
| `DEBUG`                      | `false`                  | Enable SQL echo logging    |

## Monitoring

Prometheus scrapes `/metrics` endpoint every 15s. Grafana dashboards:

- **Requests per second** -- `rate(http_requests_total[1m])`
- **HTTP Errors** -- `rate(http_errors_total[1m])`
- **Latency p95** -- `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

## Project Structure

```
app/
  main.py              # FastAPI app factory
  metrics.py           # Prometheus middleware + /metrics
  api/v1/
    auth.py            # Register, login, /me
    books.py           # Search, get, create
    favorites.py       # List, add, remove favorites
  core/
    config.py          # Settings from .env
    database.py        # SQLAlchemy async engine
    security.py        # JWT + bcrypt
  models/              # SQLAlchemy models (User, Book, Favorite)
  schemas/             # Pydantic schemas
  services/
    google_books.py    # Google Books API client
  tests/               # pytest (async, real DB)
```

## License

MIT
