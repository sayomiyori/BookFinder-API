# BookFinder API

RESTful API для поиска книг (интеграция с Google Books API, избранное, JWT-аутентификация).

## Требования

- Python 3.11+
- (Опционально) PostgreSQL для продакшена; для разработки достаточно SQLite.

## Быстрый старт (шаг 1 — инициализация)

### 1. Виртуальное окружение

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Переменные окружения

```bash
copy .env.example .env
# Отредактируйте .env: SECRET_KEY и при необходимости DATABASE_URL
```

### 4. Запуск

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

## Структура проекта

```
app/
├── main.py           # точка входа FastAPI
├── core/             # конфигурация, БД, безопасность
├── models/           # SQLAlchemy модели
├── schemas/          # Pydantic схемы
├── api/v1/           # эндпоинты
├── services/         # бизнес-логика и внешние API
├── utils/            # зависимости (DI)
└── tests/            # тесты
```

Дальнейшие шаги: настройка БД и моделей, аутентификация, эндпоинты книг и избранного.
