# BookFinder API

![CI](https://github.com/sayomiyori/BookFinder-API/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/sayomiyori/BookFinder-API/graph/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)


REST API для поиска книг: Google Books, избранное, JWT. FastAPI, SQLAlchemy 2, PostgreSQL/SQLite.

## Architecture

\`\`\`
Client
  │
  ▼
FastAPI (Docker)
  ├── JWT Auth
  ├── /api/v1/books  →  Google Books API
  └── /api/v1/fav    →  PostgreSQL
  │
  ▼
GitHub Actions CI/CD
  ├── ruff lint
  ├── pytest (coverage 87%)
  └── Docker → GHCR → Railway (prod)
  │
  ▼
Prometheus + Grafana (observability)
\`\`\`

## CI/CD

Every push triggers:
1. **Lint** — ruff checks code style
2. **Tests** — pytest with real PostgreSQL (not mocks)
3. **Coverage** — reported to Codecov
4. On merge to `main`: Docker image → GHCR → Railway auto-deploy

No manual deploys. Green badge = production is up to date.

## Local development

\`\`\`bash
cp .env.example .env
docker-compose up -d
# API:     http://localhost:8000/docs
# Metrics: http://localhost:8000/metrics
\`\`\`


