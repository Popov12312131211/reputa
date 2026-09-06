# EMP-006 — Проверка реализации (backend)

Дата проверки: 2026-09-06

## Что проверено

Проверка кода эндпоинта `POST /applications/{application_id}/decision` (решение сотрудника по заявке):

- **Маршрут**: `@router.post("/{application_id}/decision")` в `app/routers/applications.py:77` — принимает `application_id` и тело запроса.
- **Проверка роли сотрудника**: `get_current_employee` в `app/api/deps.py:28` проверяет `current_user.role != ROLE_EMPLOYEE` и возвращает 403 с `MSG_EMPLOYEE_REQUIRED` для обычных пользователей. Зависимость подключена в эндпоинте.
- **Схема решения**: `ApplicationDecisionRequest` (`app/schemas/application.py:66`) с enum `ApplicationDecision` = `approve` / `reject`. Невалидное значение даёт 422 (Pydantic).
- **Обновление статуса**: при `approve` → `EMPLOYEE_APPROVED`, при `reject` → `EMPLOYEE_REJECTED` (`applications.py:96-100`). Значения статусов согласованы с константами (`constants.py:25-26`) и моделью (`models/application.py:28-29`).
- **404 если заявка не найдена**: `applications.py:85-89`.
- **409 если уже решена**: проверка `status != IN_QUEUE` → 409 с `MSG_APPLICATION_ALREADY_DECIDED` (`applications.py:90-94`).
- **422 при невалидных данных**: валидация тела через Pydantic → 422.
- **Запрет для обычного пользователя**: `get_current_employee` даёт 403, не-сотрудник не может принять решение.

## Найденные проблемы

Не найдено. Код соответствует требованиям EMP-006, статусы/константы/роли согласованы между роутером, схемами, моделью и константами.

## Результат тестов

Команда: `.\venv\Scripts\python.exe -m pytest tests/test_applications.py -v`

**Результат: 26 passed, 0 failed** (1 DeprecationWarning от anyio/starlette, не связан с кодом).

- `TestCreateApplicationEndpoint` — 14 passed
- `TestApplicationCreateValidation` — 6 passed
- `TestApplicationDecisionEndpoint` — 6 passed (approve, reject, 403 для пользователя, 404, 409, 422)

## Рекомендации (необязательно)

1. В тестах `TestApplicationDecisionEndpoint` нет теста `401` для неавторизованного пользователя на decision-эндпоинте — можно добавить для полноты покрытия.
2. `get_current_employee` использует `User.role` из БД; если роли будут расширяться (например, admin поверх employee), стоит централизовать проверку прав в одном месте.