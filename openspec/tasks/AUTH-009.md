# AUTH-009 — Принудительная сессия + запрет входа сотрудника через обычный вход

## Статус
Выполнено.

## Описание
Две части:

1. **Принудительная сессия.** Любой API-запрос на защищённом маршруте, вернувший 401 посреди работы (не только при первом заходе на /auth/me), теперь принудительно разлогинивает пользователя и уводит на экран входа. Реализовано глобальным перехватчиком 401 в `frontend/src/api.js`: `handleUntrustedAuth` вызывается во всех five-хелперах (`getJSON`/`postJSON`/`postFormData`/`putJSON`/`patchJSON`/`deleteJSON`) при `res.status === 401` на защищённом маршруте. Эндпоинты входа/регистрации (`/api/auth/login`, `/api/auth/login/employee`, `/api/auth/register`, `/api/auth/register/employee`) из перехвата исключены — их 401 приходит по «обычным» причинам (неверный логин/пароль/код), иначе login-страница вечно перезагружалась бы.

   Обработчик регистрирует `AuthProvider` (`frontend/src/contexts/AuthContext.jsx`) через `registerSessionExpiredHandler`: сбрасывает локальную сессию (`clearSession`) и делает жёсткий редирект `window.location.assign` на `/login` (для обычного пользователя) или `/loginWork` (для сотрудника — роль берётся из ref, не из замыкания). Жёсткий редирект выбран вместо мягкого `navigate`, так как `AuthProvider` живёт вне `RouterProvider` и не имеет доступа к навигации; перезагрузка страницы даёт чистый старт под свежий (или отсутствующий) cookie. Проверка выдержана на реальном сценарии: протухший JWT в cookie → любой вызов защищённого API → 401 → принудительный редирект.

2. **Запрет входа сотрудника через обычный /login.** Эндпоинт `/auth/login` отвечает 403 `MSG_EMPLOYEE_LOGIN_FORBIDDEN`, если у аккаунта роль `employee` (даже при верных логине/пароле) — сотрудник входит только через `/auth/login/employee`. На фронте форма `/login` показывает сообщение сервера как ошибку входа, добавлена явная ссылка «Вход для сотрудников» (`login.workLoginLink` → `/loginWork`). Редирект сотрудника на `ROLE_HOME[role]` из `/login` невозможен: отработавший `/auth/login` больше не возвращает employee-аккаунт.

## Затронутые файлы
- `backend/app/routers/auth.py` — роль-gate в `/auth/login` (403 для employee).
- `backend/app/core/constants.py` — `MSG_EMPLOYEE_LOGIN_FORBIDDEN`.
- `frontend/src/api.js` — перехватчик 401 + `registerSessionExpiredHandler` + список exempt-эндпоинтов.
- `frontend/src/contexts/AuthContext.jsx` — регистрация обработчика принудительного разлогина.
- `frontend/src/components/Login.jsx` — ссылка «Вход для сотрудников».
- `frontend/src/locales/ru.json` — ключ `login.workLoginLink`.
- `backend/tests/test_auth.py` — тест `test_login_employee_forbidden`.
- `backend/tests/test_auth_me_e2e.py`, `backend/tests/test_auth_logout_delete.py` — вход сотрудника через `/auth/login/employee`.

## Проверка
- `python -m pytest` в `backend/` — 202 passed.
- `npm run build` в `frontend/` — успешно.
- Сценарий из описания: сотрудник с верными логином/паролем на `/auth/login` получает 403; вход работает только через `/auth/login/employee` с кодом.
- Протухшая/невалидная JWT-кука на защищённом маршруте → 401 → принудительный редирект на `/login` (или `/loginWork` для сотрудника).
- Эндпоинты входа/регистрации НЕ триггерят принудительное разлогинивание (исключены из перехвата).

## Что осталось
- Ничего по задаче. См. AUTH-010/AUTH-011 (регистрация сотрудников).

## Блокеры
- Нет.