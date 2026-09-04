# INFRA-003 — Модель User + миграция

## Статус
Выполнено.

## Что сделано
- Декларативный базовый класс `Base` в `backend/app/db/base.py` (SQLAlchemy 2.0 `DeclarativeBase`).
- Модель `User` в `backend/app/models/user.py`: id, ФИО, дата рождения, логин (уникальный, индексированный), хеш пароля, номер телефона, телеграм, роль (пользователь/сотрудник), created_at/updated_at.
- Константы ролей и лимитов полей в `backend/app/core/constants.py` (по правилу RULES.md — магические значения вынесены из бизнес-логики).
- Инициализирован Alembic: `alembic.ini`, `alembic/env.py` (подключён к `DATABASE_URL` из настроек и метаданным моделей), `alembic/script.py.mako`.
- Начальная миграция `0001_create_users_table.py` — создание таблицы `users`.
- `backend/app/db/session.py` — добавлен re-export `Base`.
- Тесты `backend/tests/test_user.py` — роли, лимиты пароля, roundtrip модели (SQLite in-memory).

## Затронутые файлы
- backend/app/core/constants.py
- backend/app/db/base.py
- backend/app/models/__init__.py
- backend/app/models/user.py
- backend/app/db/session.py
- backend/alembic.ini
- backend/alembic/env.py
- backend/alembic/script.py.mako
- backend/alembic/versions/0001_create_users_table.py
- backend/tests/test_user.py
- openspec/TASKS.md (отметка INFRA-003)

## Проверка
- `python -m pytest tests -q` — 3 passed.
- `python -c "from app.main import app"` — импорт без ошибок.
- `alembic upgrade head --sql` — генерирует корректный PostgreSQL DDL для таблицы `users`.

## Осталось / следующий шаг
- Следующая задача: INFRA-005 (модель ScoreResult).

## Блокеры
- Нет (локальный Postgres развёрнут через `docker compose`, миграция применена).
