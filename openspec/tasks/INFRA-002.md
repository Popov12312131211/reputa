# INFRA-002 — Фронтенд-скелет (React)

## Статус
Выполнено.

## Что сделано
- Vite + React 18 проект в `frontend/` с роутингом (react-router-dom v6).
- Все известные маршруты из TASKS.md заведены в `frontend/src/App.jsx` как страницы-заглушки (заголовок маршрута).
- Переиспользуемый компонент заглушки `frontend/src/components/PlaceholderPage.jsx` — единая заглушка без дублирования.
- Подключена заготовка i18next (react-i18next + browser-languagedetector) с русским namespace `locales/ru.json`.
- Vite dev-proxy `/api` → бэкенд `127.0.0.1:8000`.
- `.gitignore` для node_modules/dist/env.

## Затронутые файлы
- frontend/package.json
- frontend/vite.config.js
- frontend/index.html
- frontend/.gitignore
- frontend/src/main.jsx
- frontend/src/App.jsx
- frontend/src/i18n.js
- frontend/src/components/PlaceholderPage.jsx
- frontend/src/locales/ru.json
- openspec/TASKS.md (отметка INFRA-002)

## Проверка
- `npm install` — успешно (75 пакетов).
- `npm run build` — успешно, 53 модуля, сборка vite v6.4.3.

## Осталось / следующий шаг
- Маршруты с query-параметрами (`/user/my?menu={id}`, `/employee/application?menu={id}`) обрабатываются теми же путями `/user/my`, `/employee/application` — детальная карточка с `menu={id}` реализуется на этапах APP-005 / EMP-005.
- Следующие задачи: INFRA-003 (модель User), COMP-001 (общий компонент меню).

## Блокеры
- npm предупредил о неразрешённом postinstall-скрипте esbuild (allow-scripts), но сборка прошла успешно, блокером не является.
