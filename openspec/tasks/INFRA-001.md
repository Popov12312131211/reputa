# INFRA-001 — Бэкенд-скелет (FastAPI + Postgres)

## Статус
Выполнено.

## Что сделано
- FastAPI-приложение `backend/app/main.py` с эндпоинтом `/health`, возвращающим статус подключения к БД.
- `backend/app/core/config.py` — настройки через pydantic-settings из переменных окружения (`.env`), включая `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`.
- `backend/app/db/session.py` — SQLAlchemy engine (`pool_pre_ping`), фабрика сессий `SessionLocal`, зависимость `get_db`, функция `check_db_connection`.
- `backend/requirements.txt` — зависимости: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic-settings, python-dotenv, alembic.
- `backend/.env.example` — шаблон переменных окружения.

## Затронутые файлы
- backend/app/__init__.py
- backend/app/main.py
- backend/app/core/__init__.py
- backend/app/core/config.py
- backend/app/db/__init__.py
- backend/app/db/session.py
- backend/requirements.txt
- backend/.env.example
- openspec/TASKS.md (отметка INFRA-001)

## Проверка
- `pip install -r requirements.txt` — успешно.
- `python -c "from app.main import app"` — импорт без ошибок.
- `uvicorn app.main:app` — приложение стартует, `GET /health` возвращает 200.
- Ответ `/health`: `{"status":"error","database":"disconnected"}` — корректно, т.к. локальный Postgres не развёрнут.

## Осталось / следующий шаг
- Развернуть локальный Postgres и указать `DATABASE_URL` в `.env` — тогда `/health` вернёт `database: connected`.
- Управление состоянием БД (миграции Alembic, модели) — за задачи INFRA-003/004/005.

## Блокеры
Нет.
