# AUTH-001 — Регистрация (backend)

## Статус
Выполнено.

## Что сделано
- Эндпоинт `POST /auth/register` (FastAPI) в `app/routers/auth.py`: принимает ФИО, дату рождения, логин, пароль, номер телефона, телеграм; проверяет уникальность логина; хеширует пароль через bcrypt (passlib); создаёт пользователя с ролью `user`. `commit` обёрнут в `try/except IntegrityError` с `rollback()` и маппингом на 409 (закрыт race-условие check-then-insert).
- Pydantic-схемы в `app/schemas/auth.py`: `RegisterRequest` (с валидацией формата всех полей), `RegisterResponse`.
- Сервис хеширования пароля в `app/services/auth.py`: `CryptContext(schemes=[PWD_SCHEME_BCRYPT])` (константа схемы вместо литерала).
- Константы валидации пароля и лимиты полей в `app/core/constants.py` (магические числа не в бизнес-логике): `PHONE_MIN_DIGITS`, `PHONE_MAX_DIGITS`, `PHONE_PATTERN` (собирается из лимитов), `TELEGRAM_PREFIX`, `USER_MAX_AGE_YEARS`, `MSG_USER_ALREADY_EXISTS` и др.
- Хелпер `_strip_required` в схемах вместо дублирования strip+empty; телефон через `PHONE_PATTERN`, telegram через `TELEGRAM_PREFIX`; валидатор `birth_date` (будущее и возраст >150 → 422).
- `app/models/user.py`: `UserRole.EMPLOYEE = ROLE_EMPLOYEE` вместо хардкода.
- Роутер подключён в `app/main.py`.
- Зависимости `passlib[bcrypt]`, `bcrypt` добавлены в `requirements.txt`.

## Затронутые файлы
- backend/app/routers/auth.py
- backend/app/schemas/auth.py (+ __init__.py)
- backend/app/services/auth.py (+ __init__.py)
- backend/app/routers/__init__.py
- backend/app/core/constants.py
- backend/app/models/user.py
- backend/app/main.py
- backend/requirements.txt
- backend/tests/test_auth.py
- openspec/TASKS.md (AUTH-001 → done)

## Проверка
- Unit-тесты в `backend/tests/test_auth.py` на моках (без реальной БД): успешная регистрация, дубликат логина (в т.ч. race → 409 + rollback), ошибки валидации пароля (длина min/max, отсутствие заглавной/строчной/цифры/спецсимвола), неверный телефон, телеграм без `@`, пустые ФИО/логин, будущая дата → 422, дата 1800 → 422.
- `python -m pytest tests -q` в `backend/` — **29 passed** (без ослаблений/удалений тестов).
- Текущий полный прогон набора (после всех AUTH-задач и рефакторинга): **63 passed**.

## Осталось / следующий шаг
- Задача закрыта. Следующая по плану — AUTH-002 (вход пользователя, JWT в httpOnly cookie).

## Блокеры / известные ограничения (не чинить сейчас)
- `config.py`: дефолтные `JWT_SECRET`/`DATABASE_URL` и закоммиченный `backend/.env` (в `.gitignore` его нет) — решается в AUTH-002 вместе с JWT; перед продом задать собственный `JWT_SECRET`.
- Нет rate-limit на `/register` (перебор логинов через 409, спам аккаунтов).
- `phone`/`telegram` не проверяются на уникальность, только `login`.