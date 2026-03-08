# Пошаговый ручной тест BookFinder API

Сервер должен быть запущен: `uvicorn app.main:app --reload --port 8080`

Базовый URL: **http://localhost:8080**

Можно тестировать через **Swagger UI** (http://localhost:8080/docs) или через PowerShell/curl.

---

## 1. Проверка доступности

### 1.1 Health

- **Метод:** GET  
- **URL:** http://localhost:8080/health  

**Ожидание:** статус 200, тело например:
```json
{"status": "ok", "service": "BookFinder API"}
```

### 1.2 Корень (редирект на документацию)

- **Метод:** GET  
- **URL:** http://localhost:8080/  

**Ожидание:** редирект 307 на `/docs`.

---

## 2. Аутентификация

**Важно:** Регистрация и логин — это запросы **POST с телом (JSON)**. Если просто открыть ссылку в браузере, уйдёт запрос **GET** и сервер вернёт **405 Method Not Allowed**. Нужно вызывать эндпоинт из **Swagger UI** (кнопка «Try it out» → ввести тело → «Execute») или из REST-клиента / PowerShell (см. раздел 7).

**Токен в Swagger:** эндпоинты с замком (например `/me`, добавление книги, избранное) требуют заголовок с токеном. Нажми **Authorize** (замок вверху). В открывшемся окне будут поля **username** и **password**: введи тот же email и пароль, что при регистрации/логине, нажми **Authorize** — Swagger сам получит токен и будет подставлять его ко всем защищённым запросам.

### 2.1 Регистрация

- **Метод:** POST (не GET).  
- **URL:** http://localhost:8080/api/v1/auth/register  

**Как сделать в Swagger:** Открой http://localhost:8080/docs → найди **POST /api/v1/auth/register** → нажми **Try it out** → в поле Request body вставь JSON ниже → нажми **Execute**.

**Тело (JSON):**
```json
{
  "email": "test@example.com",
  "password": "testpass123"
}
```

**Ожидание:** статус 200, в ответе `access_token` и `token_type: "bearer"`.  
Скопируй **access_token** — он понадобится для следующих шагов.

Повторная регистрация с тем же email → **400** «Пользователь с таким email уже зарегистрирован».

---

### 2.2 Вход (логин)

- **Метод:** POST  
- **URL:** http://localhost:8080/api/v1/auth/login  
- **Тело (JSON):**
```json
{
  "email": "test@example.com",
  "password": "testpass123"
}
```

**Ожидание:** статус 200, новый `access_token`.

Неверный пароль или несуществующий email → **401** «Неверный email или пароль».

---

### 2.3 Текущий пользователь (me)

Эндпоинт требует токен. В Swagger он задаётся через **Authorize**.

**Как авторизоваться в Swagger:**

1. Вверху страницы http://localhost:8080/docs нажми **Authorize** (иконка замка).
2. В диалоге появятся поля **username** и **password** (не «Value»).
3. В **username** введи свой email (например `test@example.com`), в **password** — пароль (тот же, что при регистрации).
4. Нажми **Authorize**, затем **Close**. Swagger отправит запрос на вход и сохранит токен — он будет подставляться ко всем эндпоинтам с замком.
5. Открой **GET /api/v1/auth/me** → **Try it out** → **Execute**.

- **Метод:** GET  
- **URL:** http://localhost:8080/api/v1/auth/me  

**Ожидание:** статус 200, в ответе объект пользователя: `id`, `email`, `is_active`, `created_at`.

Без авторизации (не нажал Authorize или неверный email/пароль) → **401**.

---

## 3. Книги

### 3.1 Поиск книг

- **Метод:** GET  
- **URL:** http://localhost:8080/api/v1/books?q=python&page=1&limit=20  

**В Swagger:** открой **GET /api/v1/books** → **Try it out** → введи в поле **q** запрос (например `python`), в **page** — `1`, в **limit** — `20` → **Execute**.

**Ожидание:** статус 200, в теле поля `items` (массив книг), `total`, `page`, `limit`.  
При первом запросе при нехватке данных в БД идёт запрос в Google Books; новые книги сохраняются в кеш.

- Если **items пустой** и **total = 0** — возможно, исчерпана квота Google Books (429). Тогда сначала добавь книгу вручную (шаг 3.3) и снова выполни поиск по слову из названия (например `ручная` или `тест`) — книга найдётся в локальной БД.
- Без параметра **q** или с пустым **q** → **422** (валидация).

Запомни **id** любой книги из `items` (например `id: 1`) — пригодится для шагов 3.2 и 4.

---

### 3.2 Детали книги по id

- **Метод:** GET  
- **URL:** http://localhost:8080/api/v1/books/1  
(подставь реальный `id` из поиска, например 1, 2, …)

**Ожидание:** статус 200, полный объект книги.

Несуществующий id (например 99999) → **404** «Книга не найдена».

---

### 3.3 Ручное добавление книги (требуется токен)

- **Метод:** POST  
- **URL:** http://localhost:8080/api/v1/books  
- **Заголовок:** `Authorization: Bearer <твой_access_token>`  
- **Тело (JSON):**
```json
{
  "google_books_id": "manual-test-1",
  "title": "Ручная тестовая книга",
  "authors": ["Автор Тестов"],
  "isbn": "978-5-00000-000-0",
  "description": "Описание для ручного теста"
}
```

**Ожидание:** статус **201**, в ответе созданная книга с полями `id`, `google_books_id`, `title` и т.д.

Без токена → **401**.  
Повторный запрос с тем же `google_books_id` → **400** «Книга с таким google_books_id уже существует».

Запомни **id** созданной книги для раздела «Избранное».

---

## 4. Избранное (все запросы с токеном)

Заголовок для всех пунктов: `Authorization: Bearer <твой_access_token>`.

### 4.1 Список избранного

- **Метод:** GET  
- **URL:** http://localhost:8080/api/v1/users/me/favorites?page=1&limit=20  

**Ожидание:** статус 200, тело с полями `items`, `total`, `page`, `limit`.  
Сразу после регистрации `items` пустой, `total` = 0.

Без токена → **401**.

---

### 4.2 Добавить книгу в избранное

- **Метод:** POST  
- **URL:** http://localhost:8080/api/v1/users/me/favorites/1  
(подставь реальный `book_id` из поиска или из шага 3.3)

**Ожидание:** статус **201**, тело например: `{"message": "Книга добавлена в избранное", "book_id": 1}`.

Повторный POST с тем же `book_id` → **400** «Книга уже в избранном».  
Несуществующий `book_id` → **404** «Книга не найдена».

---

### 4.3 Список избранного снова

- **Метод:** GET  
- **URL:** http://localhost:8080/api/v1/users/me/favorites  

**Ожидание:** статус 200, в `items` — минимум одна запись: объект с полями `book` (полная книга) и `added_at`.

---

### 4.4 Удалить книгу из избранного

- **Метод:** DELETE  
- **URL:** http://localhost:8080/api/v1/users/me/favorites/1  
(тот же `book_id`, что добавляли)

**Ожидание:** статус **204** без тела.

Повторный DELETE или несуществующий в избранном `book_id` → **404** «Книга не найдена в избранном».

---

### 4.5 Список избранного после удаления

- **Метод:** GET  
- **URL:** http://localhost:8080/api/v1/users/me/favorites  

**Ожидание:** статус 200, `items` пустой (или без этой книги), `total` уменьшился.

---

## 5. Краткая сводка эндпоинтов

| Раздел        | Метод | Путь | Токен | Ожидаемый статус |
|---------------|-------|------|-------|-------------------|
| Health        | GET   | /health | —   | 200 |
| Регистрация   | POST  | /api/v1/auth/register | — | 200 |
| Логин         | POST  | /api/v1/auth/login | — | 200 |
| Текущий юзер  | GET   | /api/v1/auth/me | да | 200 |
| Поиск книг    | GET   | /api/v1/books?q=...&page=1&limit=20 | — | 200 |
| Книга по id   | GET   | /api/v1/books/{id} | — | 200 |
| Создать книгу | POST  | /api/v1/books | да | 201 |
| Список избр.  | GET   | /api/v1/users/me/favorites | да | 200 |
| Добавить в избр. | POST | /api/v1/users/me/favorites/{book_id} | да | 201 |
| Удалить из избр. | DELETE | /api/v1/users/me/favorites/{book_id} | да | 204 |

---

## 6. Частые ошибки

| Код | Причина | Что делать |
|-----|--------|------------|
| **405 Method Not Allowed** | Отправлен GET вместо POST (например, открыли URL в браузере). | Регистрация и логин — только **POST** с JSON-телом. Используй Swagger (Try it out → Execute) или PowerShell с `-Method Post` и `-Body`. |
| **401 Unauthorized** | Нет заголовка `Authorization: Bearer <token>` или токен неверный/истёк. | Получить новый токен через логин, в Swagger нажать Authorize и вставить токен. |
| **422 Unprocessable Entity** | Неверное тело или параметры. | Для регистрации/логина — JSON с `email` и `password`. Для **GET /api/v1/books** обязательно заполни параметр **q** (например `python`), иначе 422. |

---

## 7. Тест через PowerShell (примеры)

Убедись, что сервер запущен. Токен подставь сам.

```powershell
# Health
Invoke-RestMethod -Uri "http://localhost:8080/health"

# Регистрация
$body = '{"email":"test2@example.com","password":"testpass123"}' | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/auth/register" -Method Post -Body $body -ContentType "application/json"

# Логин (сохранить токен из ответа)
$loginBody = '{"email":"test2@example.com","password":"testpass123"}' | ConvertTo-Json
$loginResp = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginResp.access_token

# Me (с токеном)
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/auth/me" -Headers $headers

# Поиск книг
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/books?q=python&page=1&limit=5"

# Книга по id
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/books/1"

# Список избранного
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/users/me/favorites" -Headers $headers

# Добавить в избранное (book_id=1)
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/users/me/favorites/1" -Method Post -Headers $headers

# Удалить из избранного
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/users/me/favorites/1" -Method Delete -Headers $headers
```

**Важно для регистрации и логина:** обязательно указывай `-Method Post` и передавай тело в `-Body` с `-ContentType "application/json"`, иначе будет 405.

После прохождения всех шагов можно считать ручной тест выполненным.
