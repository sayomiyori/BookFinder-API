# BookFinder API

REST API для поиска книг: Google Books, избранное, JWT. FastAPI, SQLAlchemy 2, PostgreSQL/SQLite.

---

## Быстрый старт

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate    # Linux/macOS

pip install -r requirements.txt
cp .env.example .env           # заполнить SECRET_KEY и при необходимости DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Документация:** http://localhost:8000/docs  
**Проверка:** http://localhost:8000/health

---

## Docker

```bash
docker compose up --build
```

API: http://localhost:8001/docs (порт 8001, чтобы не конфликтовать с локальным запуском).

---

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Проверка доступности |
| POST | `/api/v1/auth/register` | Регистрация → токен |
| POST | `/api/v1/auth/login` | Вход → токен |
| GET | `/api/v1/auth/me` | Текущий пользователь (Bearer) |
| GET | `/api/v1/books?q=&page=1&limit=20` | Поиск книг |
| GET | `/api/v1/books/{id}` | Книга по id |
| POST | `/api/v1/books` | Добавить книгу (Bearer) |
| GET | `/api/v1/users/me/favorites` | Избранное (Bearer) |
| POST | `/api/v1/users/me/favorites/{book_id}` | В избранное |
| DELETE | `/api/v1/users/me/favorites/{book_id}` | Удалить из избранного |

Ручное тестирование: [MANUAL_TEST.md](MANUAL_TEST.md).

---

## Тесты

```bash
pytest app/tests -v
pytest app/tests -v --cov=app --cov-report=term-missing
```

---

## Структура

```
app/
├── main.py
├── core/          # config, database, security
├── models/        # User, Book, Favorite
├── schemas/       # Pydantic
├── api/v1/        # auth, books, favorites
├── services/      # google_books
├── utils/         # get_db, get_current_user
└── tests/
alembic/           # миграции
```

---

## Настройка

Переменные окружения задаются в `.env` (см. `.env.example`). Основные:

- `SECRET_KEY` — для JWT (обязательно сменить в production).
- `DATABASE_URL` — SQLite для разработки или PostgreSQL для production.
- `CORS_ORIGINS` — разрешённые origins через запятую.

Токены и пароли в репозиторий не коммитить; `.env` в `.gitignore`.

---


