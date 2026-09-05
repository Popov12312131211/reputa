# AUTH-004 — Страница регистрации (frontend `/registration/`)

## Что сделано
- Создан компонент `Registration.jsx` + `Registration.css` по макету `frontend-temp/registration`: карточка, поля, показ/скрытие пароля, живая подсказка требований к паролю, маски телефона и даты, автоподстановка `@` для телеграма.
- Все строки интерфейса вынесены в i18n (namespace `registration` в `ru.json`).
- Константы валидации — в `src/constants/auth.js` (границы пароля, правила, маска телефона, ограничения даты).
- Валидация: ФИО (≥ 3 слов), дата рождения (формат, реальная дата, возраст ≥ 18), логин, пароль (8–64, A-z/a-z, цифры, спецсимволы `!@#$_`), повтор пароля, телефон (маска `+7(XXX)XXX-XX-XX`), телеграм (`@username`).
- Регистрация подключена к AUTH-001 (`POST /api/auth/register`) через `postJSON` из `frontend/src/api.js`. Перед отправкой телефон нормализуется `+7(999)000-00-00` → `+79990000000` (бэкенд принимает `^\+?\d{7,15}$`), дата `дд.мм.гггг` → ISO `гггг-мм-дд`. При успехе — переход на `/login`, при ошибке — сообщение через i18n-ключ `registration.error`.
- Маршрут `/registration` в `App.jsx` переведён с `PlaceholderPage` на `Registration`.

## Затронутые файлы
- frontend/src/constants/auth.js
- frontend/src/components/Registration.jsx
- frontend/src/components/Registration.css
- frontend/src/api.js
- frontend/src/App.jsx
- frontend/src/locales/ru.json
- openspec/TASKS.md

## Проверка
- `npm run build` (vite): сборка успешна.
- Бэкенд-тесты `python -m pytest tests -q`: 63 passed.

## Что осталось
- Подтверждение номера и телеграма — осознанно вне объёма MVP.

## Блокеры
- Нет. Зависимость от AUTH-001 (backend) закрыта.