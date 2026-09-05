# AUTH-007 — Защита приватных маршрутов

## Статус
Выполнено. Ожидает AUTH-002/AUTH-003 (эндпоинты входа) для сквозной проверки.

## Что сделано

### Бэкенд
- `services/auth.py`: добавлены `create_access_token(user_id, role)` и `decode_access_token(token)` на PyJWT (HS256, TTL из `settings.JWT_EXPIRE_MINUTES`). Используются middleware и эндпоинтом `/auth/me`; `create_access_token` будет переиспользован AUTH-002/003.
- `core/constants.py`: константы `COOKIE_NAME = "access_token"`, `MSG_NOT_AUTHENTICATED = "Не авторизован"`.
- `main.py`: `@app.middleware("http")` — защищает префиксы `/user/` (роль `user`) и `/employee/` (роль `employee`): проверяет JWT из cookie и роль из payload, при несоответствии — 401. Работает для всех будущих эндпоинтов под этими префиксами без дополнительной wiring.
- `routers/deps.py` (новый): dependency `get_current_user` — читает cookie, декодирует JWT, грузит пользователя из БД, отдаёт 401 при невалидном токене/отсутствии пользователя.
- `routers/auth.py`: эндпоинт `GET /auth/me` (ответ `MeResponse`: id, full_name, role) — для восстановления сессии на фронтенде (контракт из AUTH-005/006).
- `requirements.txt`: `PyJWT==2.10.1` (python-jose устаревший и неподдерживаемый — выбран поддерживаемый аналог).

### Фронтенд
- `contexts/AuthContext.jsx`: провайдер теперь загружает сессию через `GET /api/auth/me` (с `credentials: 'include'`) и отдаёт `user`, `role` (из данных пользователя), `loading`. Роль больше не вычисляется из URL-пути.
- `components/RequireAuth.jsx` (новый): route guard — пока идёт проверка сессии возвращает null; гости `/user/*` уходят на `/login`, гости `/employee/*` — на `/loginWork`; при несовпадении роли с префиксом пути → редирект в кабинет своей роли (`/employee/settings` или `/user/my`), неизвестная роль → `/login`. Иначе рендерит `Layout`.
- `App.jsx`: защищённые маршруты обёрнуты в `<AuthProvider><RequireAuth /></AuthProvider>`.

### Прокси-слой (необходимо для контракта `/api/auth/me`)
- `vite.config.js`: добавлен `rewrite`, срезающий префикс `/api`.
- `nginx.conf`: `proxy_pass http://backend:8000/` (слеш) — `location /api/` срезает префикс.

## Рефакторинг
- Backend: общий helper 401 в `get_current_user`; middleware защищает и голые `/user`, `/employee`, но не похожие пути вроде `/userprofile`.
- Frontend: гости `/employee/*` направляются на `/loginWork`; неизвестная роль направляется на `/login`, а не в возможный цикл редиректов.

## Затронутые файлы
- backend/app/services/auth.py
- backend/app/core/constants.py
- backend/app/main.py
- backend/app/routers/deps.py (новый)
- backend/app/routers/auth.py
- backend/app/schemas/auth.py
- backend/requirements.txt
- backend/tests/test_auth_007.py (новый)
- frontend/src/contexts/AuthContext.jsx
- frontend/src/components/RequireAuth.jsx (новый)
- frontend/src/App.jsx
- frontend/vite.config.js
- frontend/nginx.conf
- openspec/TASKS.md — AUTH-007 отмечена выполненной

## Проверка
- `python -m pytest` (backend): **43 passed** (29 существующих + 14 на AUTH-007, включая регрессию границ приватных префиксов).
- Фронтенд-сборка не запускалась: в текущей среде не установлен Node.js (`npm`/`node` отсутствуют в PATH). Проверен только код статически.

## Что осталось
- AUTH-002 (вход пользователя) и AUTH-003 (вход сотрудника): после их реализации фронтенд сохранит пользователя в AuthContext после логина, и защищённые страницы откроются.
- В `Login.jsx`/`LoginWork.jsx` — заменить заглушки на реальные запросы с `credentials: 'include'` (TODO уже размечены там).

## Блокеры
- Для сквозной проверки (вход → доступ к приватным страницам) нужна хотя бы одна из задач AUTH-002/AUTH-003.