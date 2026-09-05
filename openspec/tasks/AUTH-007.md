# AUTH-007 — Защита приватных маршрутов

## Статус
Выполнено. Ожидает AUTH-002/AUTH-003 (эндпоинты входа) для сквозной проверки.

## Что сделано

### Бэкенд
- `services/auth.py`: добавлены `create_access_token(user)` (принимает объект `User`, в JWT кладёт `sub`=id, `role`) и `decode_access_token(token)` на PyJWT (HS256, TTL из `settings.JWT_EXPIRE_MINUTES`). Используются middleware и эндпоинтом `/auth/me`; `create_access_token` переиспользован AUTH-002/003.
- `core/constants.py`: константы `COOKIE_NAME = "access_token"`, `MSG_NOT_AUTHENTICATED = "Не авторизован"`.
- `main.py`: `@app.middleware("http")` — защищает префиксы `/user/` (роль `user`) и `/employee/` (роль `employee`): проверяет JWT из cookie и роль из payload, при несоответствии — 401. Работает для всех будущих эндпоинтов под этими префиксами без дополнительной wiring.
- `routers/deps.py` (новый): dependency `get_current_user` — читает cookie, декодирует JWT, грузит пользователя из БД, отдаёт 401 при невалидном токене/отсутствии пользователя.
- `routers/auth.py`: эндпоинт `GET /auth/me` (ответ `MeResponse`: id, full_name, role) — для восстановления сессии на фронтенде. Поле `role` добавлено в `MeResponse` позже (см. заметку ниже).
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
- AUTH-002 (вход пользователя) и AUTH-003 (вход сотрудника): фронтенд после логина сохраняет пользователя в AuthContext и переходит в кабинет своей роли.
- В `Login.jsx`/`LoginWork.jsx`/`Registration.jsx` заглушки `serverNotReady` заменены реальными запросами с `credentials: 'include'` (через общий хелпер `frontend/src/api.js`).

## Заметка о контракте `/auth/me`
- `MeResponse` не содержал поля `role`, хотя контракт (этот файл и AUTH-005/006) и фронтенд (`AuthContext`, `RequireAuth`) его требуют. Из-за этого восстановление сессии при перезагрузке давало пользователя без роли, и guard отправлял даже авторизованного на `/login`. Поле `role` добавлено в `backend/app/schemas/auth.py`; в `test_auth_007.py` хелпер `_token` приведён к актуальной сигнатуре `create_access_token(user)`.

## Блокеры
- Нет. Сквозной сценарий «вход → доступ к приватным страницам» реализуем (требует поднятого backend и frontend).