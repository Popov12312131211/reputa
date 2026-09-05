# AUTH-003 — Вход для сотрудников (backend)

## Статус
Выполнено.

## Что сделано
- В `app/core/constants.py` — `STAFF_LOGIN_CODE = "123456"` и сообщения `MSG_INVALID_STAFF_CODE`, `MSG_NOT_EMPLOYEE`.
- В `app/schemas/auth.py` общая валидация логина/пароля вынесена в базовый класс `_CredentialsBase` (используется `LoginRequest`), добавлен `EmployeeLoginRequest` (login + code + password, код только непустой).
- В `app/routers/auth.py`:
  - выдача JWT-куки вынесена в переиспользуемый `_set_auth_cookie(response, user)` — используется обоими эндпоинтами входа;
  - добавлен `POST /auth/login/employee`: проверка кода (первой, до запросов БД), затем логин/пароль (единый ответ 401 как в обычном входе), затем проверка роли (403 для не-сотрудников), выдача httpOnly cookie.
  - в `POST /auth/register` добавлен bootstrap: если в БД нет ни одного пользователя (`count() == 0`), первый зарегистрированный получает роль `employee` — иначе `user`.

## Затронутые файлы
- backend/app/core/constants.py (+STAFF_LOGIN_CODE, сообщения)
- backend/app/schemas/auth.py (+_CredentialsBase, EmployeeLoginRequest)
- backend/app/routers/auth.py (+POST /auth/login/employee, _set_auth_cookie, bootstrap в register)
- backend/tests/test_auth.py (+bootstrap и employee-login тесты)
- openspec/TASKS.md (AUTH-003 → done)

## Проверка
- `pytest tests/` — **49 passed** (было 37). Добавлено 12: bootstrap (первый регистратор = employee, при наличии пользователей = user), employee login (успех с cookie, JWT с role=employee, обрезка логина, неверный код 401, неверный пароль 401, неизвестный логин 401, несотрудник 403, код проверяется до БД, пустые код/пароль 422).
- Текущий полный прогон набора (после всех AUTH-задач и рефакторинга): **63 passed**.

## Сквозная проверка в Docker
- Данные сброшены (`TRUNCATE users RESTART IDENTITY CASCADE`), backend пересобран:
  - первый `POST /auth/register` → 201, `role:"employee"` (bootstrap);
  - `POST /auth/login/employee` (anna, 123456) → 200 + httpOnly cookie, JWT `role:"employee"`, TTL 24 ч;
  - второй `POST /auth/register` → 201, `role:"user"`;
  - `POST /auth/login/employee` для обычного пользователя → 403 «Вход разрешён только сотрудникам»;
  - неверный код → 401 «Неверный код».

## Осталось / передаётся дальше
- Следующая задача по Этапу 2 — AUTH-007 (защита приватных маршрутов).
- Фронтенд `LoginWork.jsx` (`/loginWork`) тогда показывал заглушку `serverNotReady` — теперь подключён к `POST /auth/login/employee` (см. рефакторинг-отчёт и AUTH-006.md).
- Эндпоинт отправки SMS-кода не предусмотрен (MVP): кнопка «Отправить код» остаётся без действия.

## Блокеры
- Нет.