# ─────────────────────────────────────────────────────────────────────────────
# BookFinder API — Multi-stage Docker build
#
# Stage 1 (builder): компилирует Python-зависимости в /install
# Stage 2 (runtime): минимальный образ без build-инструментов
#
# Размер итогового образа значительно меньше, чем при однослойной сборке.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Системные пакеты для компиляции (gcc нужен для psycopg2, hiredis и пр.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости в изолированный prefix /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Только runtime-библиотека PostgreSQL (libpq5), без gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем скомпилированные зависимости из builder-стадии
COPY --from=builder /install /usr/local

# Копируем исходный код приложения
COPY app/ ./app/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Настройки Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Непривилегированный пользователь для безопасности
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Entrypoint: миграции БД + uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
