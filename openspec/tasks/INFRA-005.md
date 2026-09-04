# INFRA-005 — Модель ScoreResult + миграция

## Статус
Выполнено.

## Что сделано
- Константы в `backend/app/core/constants.py`: границы метрик психологического портрета (0–10).
- Модель `ScoreResult` в `backend/app/models/score_result.py` (SQLAlchemy 2.0): id, `application_id` (FK → applications.id, ON DELETE CASCADE, индекс), списки позитивных сигналов и факторов риска (JSON), три метрики портрета (стабильность, финансовая грамотность, ответственность — 0–10), отчёт для комитета (Text) + дата последнего обновления, итоговая оценка (0–100), created_at/updated_at. Связь `application` ↔ `score_result` (один-к-одному).
- Модель `Application` — добавлена relationship `score_result` (обратная сторона, `uselist=False`).
- `backend/app/models/__init__.py` — экспорт `ScoreResult`.
- Миграция `0003_create_score_results_table.py` — создание таблицы `score_results` + индекс на `application_id` + FK.
- Тесты `backend/tests/test_score_result.py` — границы метрик и оценки, roundtrip модели, relationship и FK.

## Затронутые файлы
- backend/app/core/constants.py
- backend/app/models/score_result.py (новый)
- backend/app/models/application.py (relationship)
- backend/app/models/__init__.py
- backend/alembic/versions/0003_create_score_results_table.py
- backend/tests/test_score_result.py (новый)
- openspec/TASKS.md (отметка INFRA-005)

## Проверка
- `python -m pytest tests -q` — 11 passed.
- `alembic upgrade head` — применена (0002 → 0003), таблица `score_results` с FK и индексом создана.
- `alembic downgrade 0002` / `upgrade head` — roundtrip без ошибок.
- `GET /health` — 200, `database: connected`.

## Осталось / следующий шаг
- Этап 1 завершён: модели User, Application, ScoreResult + миграции применены.
- Следующая задача: COMP-001 (общий компонент меню/сайдбара) или Этап 2 (AUTH-001 регистрация).

## Блокеры
- Нет.
