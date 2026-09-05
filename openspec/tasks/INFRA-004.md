# INFRA-004 — Модель Application + миграция

## Спецификация ID заявки
ID заявки — это первые 10 символов хеша данных заявки (детерминированная строка из случайных символов). ID **не автоинкремент** и не числовой. Правило действует для всех заявок: реальных, моков и заглушек — ID всегда выглядит как 10 случайных символов, а не как 1, 2, 3...

## Статус
Выполнено.

## Что сделано
- Константы в `backend/app/core/constants.py`: статусы заявки (в очереди / авто-одобрено / авто-отказано / одобрено сотрудником / отклонено сотрудником), лимиты полей (сумма Numeric(12,2), цель, телеграм-канал), границы оценки скоринга (0–100).
- Модель `Application` в `backend/app/models/application.py` (SQLAlchemy 2.0): id, `user_id` (FK → users.id, ON DELETE CASCADE, индексировано), сумма, цель/причина, телеграм, телеграм-канал, статус (default `in_queue`), итоговая оценка (nullable), created_at/updated_at. Связь `user` ↔ `applications`.
- Модель `User` — добавлены relationship `applications` (обратная сторона).
- `backend/app/models/__init__.py` — экспорт `Application`.
- Миграция `0002_create_applications_table.py` — создание таблицы `applications` + индекс на `user_id` + FK.
- Тесты `backend/tests/test_application.py` — статусы, границы оценки, roundtrip модели с пользователем, проверка relationship и FK.

## Затронутые файлы
- backend/app/core/constants.py
- backend/app/models/application.py (новый)
- backend/app/models/user.py (relationship)
- backend/app/models/__init__.py
- backend/alembic/versions/0002_create_applications_table.py
- backend/tests/test_application.py (новый)
- openspec/TASKS.md (отметка INFRA-004)

## Проверка
- `python -m pytest tests -q` — 7 passed.
- `alembic upgrade head` — применена (0001 → 0002), таблица `applications` с FK и индексом создана.
- `alembic downgrade 0001` / `upgrade head` — roundtrip без ошибок.
- `GET /health` — 200, `database: connected`.

## Осталось / следующий шаг
- Следующая задача: COMP-001 (общий компонент меню/сайдбара) или Этап 2 (AUTH-001 регистрация).

## Блокеры
- Нет.
