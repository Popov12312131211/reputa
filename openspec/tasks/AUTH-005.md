# AUTH-005 — Страница входа (frontend `/login/`)

## Статус
Выполнено (фронтенд). Ожидает AUTH-002 (backend).

## Что сделано
- Компонент `Login.jsx` + `Login.css` на базе макета.
- Два поля: логин (text) и пароль (password с toggle видимости).
- Клиентская валидация: оба поля обязательны (непустые).
- Ссылки: «Забыли пароль?» → `/forgot`, «Нет аккаунта? Регистрация» → `/registration`.
- Отправка — заглушка: при submit показывается `login.serverNotReady` (TODO на AUTH-002).
- Все строки интерфейса в i18n (namespace `login` в `ru.json`).
- Маршрут `/login` в `App.jsx` подключён к компоненту `Login`.

## Затронутые файлы
- `frontend/src/components/Login.jsx` (новый)
- `frontend/src/components/Login.css` (новый)
- `frontend/src/locales/ru.json` (добавлен namespace `login`)
- `frontend/src/App.jsx` (маршрут `/login`)

## Проверка
- `npm run build` — сборка прошла успешно.

---

## Эндпоинты, необходимые для подключения

### 1. AUTH-002 — Вход пользователя (main)

**POST `/api/auth/login`**

Описание: Аутентификация пользователя-заемщика по логину и паролю.

Запрос:
```json
{
  "login": "string",
  "password": "string"
}
```

Ответ — успех (200):
```json
{
  "id": 1,
  "full_name": "Иванов Иван Иванович",
  "role": "user"
}
```

Ответ — ошибка (401):
```json
{
  "detail": "Неверный логин или пароль"
}
```

Побочные эффекты:
- Устанавливает httpOnly cookie `access_token` с JWT (HS256, TTL 24 ч).
- Payload JWT: `{ "sub": "<user_id>", "role": "user" }`.

Зависимости:
- `passlib[bcrypt]` + `python-jose[cryptography]` — добавить в `requirements.txt`.
- Таблица `users` (INFRA-003) — сравнение `password_hash` через `bcrypt.verify()`.

---

### 2. AUTH-003 — Вход для сотрудников

**POST `/api/auth/login-work`**

Описание: Аутентификация сотрудника по логину, коду с телефона и паролю.

Запрос:
```json
{
  "login": "string",
  "phone_code": "string",
  "password": "string"
}
```

Ответ — успех (200):
```json
{
  "id": 1,
  "full_name": "Иванов Иван Иванович",
  "role": "employee"
}
```

Ответ — ошибка (401):
```json
{
  "detail": "Неверный логин, код или пароль"
}
```

Побочные эффекты:
- Устанавливает httpOnly cookie `access_token` с JWT (HS256, TTL 24 ч).
- Payload JWT: `{ "sub": "<user_id>", "role": "employee" }`.

Примечания:
- Дефолтный код для MVP: `"123456"`.
- Если в БД нет пользователей — первый зарегистрированный автоматически получает роль `employee`.

---

### 3. AUTH-007 (связанный) — Проверка текущей сессии

**GET `/api/auth/me`**

Описание: Возвращает данные текущего пользователя по JWT из cookie. Нужен фронтенду для восстановления сессии при перезагрузке страницы.

Ответ — авторизован (200):
```json
{
  "id": 1,
  "full_name": "Иванов Иван Иванович",
  "role": "user"
}
```

Ответ — не авторизован (401):
```json
{
  "detail": "Не авторизован"
}
```

---

### 4. AUTH-001 (связанный) — Регистрация

**POST `/api/auth/register`**

Описание: Регистрация нового пользователя. Связан с AUTH-005, т.к. страница входа ссылается на `/registration`.

Запрос:
```json
{
  "full_name": "Иванов Иван Иванович",
  "birth_date": "2000-01-15",
  "login": "IvanIvanov2000",
  "password": "StrongPass1!",
  "phone": "+7(999)123-45-67",
  "telegram": "@ivanov"
}
```

Ответ — успех (201):
```json
{
  "id": 1,
  "full_name": "Иванов Иван Иванович",
  "role": "user"
}
```

Ответ — ошибка (422 / 409):
```json
{
  "detail": "Пользователь с таким логином уже существует"
}
```

---

## Что осталось (подключение к бэкенду)

После реализации AUTH-002 в `Login.jsx` необходимо:

1. Заменить заглушку в `handleSubmit` на `POST /api/auth/login`:
   ```js
   const res = await fetch('/api/auth/login', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     credentials: 'include',
     body: JSON.stringify({ login, password })
   })
   ```

2. Обработать ответ:
   - **200** → сохранить данные пользователя в `AuthContext`, перенаправить на `/user/my` (или `/employee/settings` если `role === 'employee'`).
   - **401** → показать сообщение «Неверный логин или пароль».
   - **422** → показать ошибки валидации полей.

3. Обновить `AuthContext` для чтения роли из JWT (вместо URL-пути) — вызов `GET /api/auth/me` при загрузке приложения.

4. Добавить `credentials: 'include'` во все fetch-запросы для передачи httpOnly cookie.

## Блокеры
- AUTH-002 (backend) — эндпоинт входа по логину/паролю.
- AUTH-007 — middleware проверки JWT на бэкенде + route guard на фронтенде (иначе после входа пользователь попадёт на защищённую страницу без защиты).
