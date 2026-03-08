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

### 4. Миграции БД (Alembic)

```bash
# Применить миграции (создать таблицы)
alembic upgrade head

# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "описание"
```

Для PostgreSQL в `.env` нужен `DATABASE_URL=postgresql+asyncpg://...`. Для миграций установите `psycopg2-binary` и используйте sync-URL (Alembic подставит его сам из `database_url_sync`).

### 5. Запуск

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Примеры запросов из PowerShell

**Сначала запустите сервер** в одном терминале: `uvicorn app.main:app --reload --port 8080`.  
В другом терминале (или когда сервер уже работает) выполняйте запросы. В PowerShell URL с параметрами (`&`) передавайте в кавычках:

```powershell
# Поиск книг (порт 8080)
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/books?q=python&page=1&limit=20"

# Health
Invoke-RestMethod -Uri "http://localhost:8080/health"
```

Если видите «Невозможно соединиться с удаленным сервером» — сервер не запущен; запустите uvicorn и повторите запрос.  
Через Swagger (http://localhost:8080/docs) можно вызывать эндпоинты из браузера.

### Запуск через Docker (шаг 9)

Нужны **Docker** и **Docker Compose** (в новых версиях Docker — встроенная команда `docker compose`). В корне проекта:

```bash
docker compose up --build
```

Если у вас старая версия Docker, используйте: `docker-compose up --build`.

- Поднимается **PostgreSQL** (порт 5432) и **приложение** (порт **8001** на хосте, чтобы не конфликтовать с локальным uvicorn на 8000).
- При старте контейнера приложения автоматически выполняются миграции (`alembic upgrade head`), затем запускается uvicorn.
- API: http://localhost:8001  
- Swagger: http://localhost:8001/docs  

Учётные данные БД по умолчанию: пользователь `bookfinder`, пароль `bookfinder`, база `bookfinder`. При необходимости задайте `SECRET_KEY` в `.env` или в переменных окружения перед запуском.

Остановка: `docker compose down` (или `docker-compose down`). Данные PostgreSQL сохраняются в volume `postgres_data`.

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

- **Шаг 2–6:** БД, модели, аутентификация, книги, избранное.
- **Шаг 8:** pytest, тесты auth/books/favorites/health.
- **Шаг 9:** Dockerfile и docker-compose (app + PostgreSQL).

## Возможные ошибки

- **WinError 10013** при запуске uvicorn — порт занят или недоступен. Запустите на другом порту: `uvicorn app.main:app --reload --port 8080`.
- **GET / → 404** — по умолчанию корень `/` перенаправляет на `/docs`.
- **UnicodeDecodeError** при `alembic upgrade head` или `alembic revision` — в `DATABASE_URL` (часто в пароле) есть символ не в UTF-8, или файл `.env` сохранён в другой кодировке (например Windows-1251). Решение: сохранить `.env` в кодировке **UTF-8** и использовать в пароле только латиницу/цифры, либо для разработки задать `DATABASE_URL=sqlite+aiosqlite:///./bookfinder.db`.
- **ModuleNotFoundError: psycopg2** — при использовании PostgreSQL для миграций нужен синхронный драйвер: `pip install psycopg2-binary`.
- **В PowerShell «Амперсанд (&) не разрешен»** — в команде указан URL с `&`. Весь URL берите в **двойные кавычки**: `Invoke-RestMethod -Uri "http://localhost:8080/api/v1/books?q=python&page=1&limit=20"`.
- **«Невозможно соединиться с удаленным сервером»** — сервер (uvicorn) не запущен. В отдельном терминале выполните `uvicorn app.main:app --reload --port 8080`, затем повторите запрос.
- **Docker: «ports are not available» / «bind: Only one usage of each socket»** — порт 8000 занят (например, локальный uvicorn). В этом проекте приложение в Docker слушает порт **8001** (http://localhost:8001). Остановите процесс на 8000 или используйте 8001 для доступа к API в контейнере.
