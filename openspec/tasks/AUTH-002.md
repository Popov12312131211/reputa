# AUTH-002 — Вход пользователя (backend)

## Статус
Выполнено.

## Что сделано
- Добавлена зависимость `PyJWT==2.10.1` (`requirements.txt`).
- В `app/core/config.py` — настройки cookie: `ACCESS_TOKEN_COOKIE_NAME`, `COOKIE_SECURE` (по умолчанию false, включать только за HTTPS). В `.env.example` — комментарий про `COOKIE_SECURE`.
- В `app/core/constants.py` — `MSG_INVALID_CREDENTIALS` (единый текст для неверного логина и пароля, чтобы не раскрывать наличие аккаунта).
- В `app/services/auth.py` — `create_access_token(user)` — JWT с `sub` (id пользователя), `role`, `iat`, `exp` на основе `settings.JWT_EXPIRE_MINUTES`.
- В `app/schemas/auth.py` — `LoginRequest` (нормализация логина как при регистрации, пароль только непустой) и `LoginResponse` (тот же состав, что и `RegisterResponse`).
- В `app/routers/auth.py` — `POST /auth/login`: поиск пользователя по логину, проверка пароля, выдача JWT в httpOnly cookie (samesite=lax, path=/, max_age = сутки), ответ — данные пользователя.

## Затронутые файлы
- backend/requirements.txt (+PyJWT)
- backend/.env.example (+COOKIE_SECURE)
- backend/app/core/config.py (+cookie-настройки)
- backend/app/core/constants.py (+MSG_INVALID_CREDENTIALS)
- backend/app/services/auth.py (+create_access_token)
- backend/app/schemas/auth.py (+LoginRequest/LoginResponse)
- backend/app/routers/auth.py (+POST /auth/login)
- backend/tests/test_auth.py (+тесты логина)
- openspec/TASKS.md (AUTH-002 → done)

## Проверка
- `pytest tests/` — **37 passed**. Добавлены: успешный вход с httpOnly cookie, валидность JWT (sub/role/ttl), нормализация логина, неверный пароль, неизвестный логин, пустые поля; юнит-тест `create_access_token`.
- Текущий полный прогон набора (после всех AUTH-задач и рефакторинга): **63 passed**.

## Сквозная проверка в Docker + баг `.dockerignore`
- Сквозной сценарий (`docker compose up --build -d`): `GET /health` → `{"status":"ok","database":"connected"}`; `POST /auth/register` → 201; `POST /auth/login` → 200 + `Set-Cookie: access_token=...; HttpOnly`, TTL ровно 24 ч; неверный пароль → 401 `{"detail":"Неверный логин или пароль"}`.
- Найден и исправлен баг: `backend/.dockerignore` исключал `alembic/versions` — миграции не попадали в образ, `alembic upgrade head` в entrypoint не находил скриптов, контейнерная БД оставалась без таблиц (`relation "users" does not exist`). Строка из `.dockerignore` удалена, backend пересобран; после пересборки `alembic current` → `0003 (head)`.
- Передаётся дальше: локальный uvicorn на Windows подключался к локальному Windows-PostgreSQL (PID 7312), занимающему `5432` вместе с контейнером — при разработке вне Docker не забыть про этот конфликт либо переназначить порт.

## Осталось / передаётся дальше
- Следующая задача по Этапу 2 — AUTH-003 (вход для сотрудников по коду) и AUTH-007 (защита приватных маршрутов).
- Фронтенд `Login.jsx` тогда показывал заглушку `serverNotReady` — теперь подключён к `POST /auth/login` (см. рефакторинг-отчёт и AUTH-005.md).

## Блокеры
- Нет.