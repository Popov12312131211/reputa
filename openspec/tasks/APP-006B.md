# APP-006B — Backend для выхода и удаления аккаунта + проверка API настроек

## Статус
Выполнено.

## Описание
Задача добавлена в TASKS.md как бэклог. Реализованы реальные эндпоинты выхода и удаления аккаунта, фронтенд подключён вместо заглушек, API настроек профиля проверено на реальной БД (не только на моках).

## Что сделано

### Бэкенд
- `backend/app/routers/auth.py`:
  - `POST /auth/logout` (204) — выход: инвалидирует auth-cookie (`_clear_auth_cookie`, двойник `_set_auth_cookie` с max_age=0). JWT stateless, поэтому токен просто удаляется на клиенте. Требует авторизации (`get_current_user`).
  - `DELETE /auth/delete` (204) — удаление аккаунта: `db.delete(current_user)` + commit, затем чистит cookie. Требует авторизации.
  - Вспомогательный `_clear_auth_cookie(response)`.
- **Решение по судьбе заявок (задокументировано в коде)**: каскадное удаление. В схеме БД `applications.user_id` (`ON DELETE CASCADE`) и `score_results.application_id` (`ON DELETE CASCADE`) — удаление пользователя транзитивно удаляет его заявки и результаты скоринга. Для MVP это осознанный выбор (право на забвение, GDPR-стиль; без обезличивания и без запрета удаления при активных заявках).
- `backend/app/models/user.py`: на relationship `User.applications` добавлен `passive_deletes=True` — иначе SQLAlchemy при удалении пользователя пытался бы обнулить NOT NULL `user_id` у заявок и падал с IntegrityError вместо того, чтобы отдать каскад БД.

### Фронтенд
- `frontend/src/api.js`: добавлены хелперы `patchJSON` и `deleteJSON` (по образцу существующих).
- `frontend/src/contexts/AuthContext.jsx`: добавлен `clearSession` (сброс локального состояние сессии); разлогин cookie выполняет бэкенд.
- `frontend/src/components/UserSettings.jsx` и `EmployeeSettings.jsx`:
  - Убран мок `MOCK_PROFILE`, поля загружаются через `GET /api/auth/profile` при монтировании (телефон приводится к маске `formatPhone`).
  - Сохранение — реальный `PATCH /api/auth/profile` (телефон в формате бэкенда `+7999...`, пароль отправляется только если менялся); индикаторы загрузки/ошибок (`saving`, `loadError`, `saveError`).
  - «Выйти из аккаунта» -> `POST /api/auth/logout`, сброс сессии, переход на `/login` (user) / `/loginWork` (employee).
  - «Удалить аккаунт» -> `DELETE /api/auth/delete`, сброс сессии, переход на /login / /loginWork.
  - Перед навигацией после выхода/удаления сбрасывается `dirty` (чтобы useBlocker/beforeunload не перехватывали переход).
- `frontend/src/locales/ru.json`: ключи `userSettings.{loadError,saveError,saving}` и `employeeSettings.{profileLoadError,profileSaveError,saving}` (профильные, чтобы не конфликтовали с `employeeSettings.loadError/saveError` порогов автоматизации).

### Тесты
- `backend/tests/test_auth_logout_delete.py` (новый, 8 тестов, реальная in-memory SQLite через StaticPool — единый паттерн сквозных тестов):
  - Logout: требует авторизации (401), очищает cookie (Set-Cookie max-age=0, jar пустеет, `/auth/me` -> 401), не удаляет пользователя (повторный вход работает).
  - Delete: требует авторизации (401), удаляет пользователя и очищает cookie (повторный вход -> 401), каскадно удаляет заявки пользователя.
  - ProfileSettingsEndToEnd: GET/PATCH `/auth/profile` сквозь регистрацию/логин на реальной БД — чтение данных, обновление всех полей+пароля, вход по новым данным; PATCH без поля password оставляет пароль прежним.
  - В фикстуре включён `PRAGMA foreign_keys=ON` (повторяет поведения Postgres для проверки каскада).

## Затронутые файлы
- backend/app/routers/auth.py
- backend/app/models/user.py
- backend/tests/test_auth_logout_delete.py (новый)
- frontend/src/api.js
- frontend/src/contexts/AuthContext.jsx
- frontend/src/components/UserSettings.jsx
- frontend/src/components/EmployeeSettings.jsx
- frontend/src/locales/ru.json

## Проверка
- `./venv/Scripts/python.exe -m pytest` в `backend/` — 187 passed.
- `npm run build` в `frontend/` — сборка Vite проходит успешно.

## Что осталось
- Ручная проверка в браузере: подтверждение удаления/выхода (сейчас без диалога-подтверждения — кнопки сразу выполняются, в задаче это не отдельно требовалось).
- AUTH-009 (принудительный редирект при истёкшей сессии) — отдельная задача, не входит в APP-006B.

## Блокеры
- Нет.
