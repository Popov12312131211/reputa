# COMP-001 — Общий компонент меню/сайдбара (frontend)

## Статус
Выполнено.

## Что сделано
- Установлен `lucide-react` (пакет из задания, единственная новая зависимость).
- Добавлен namespace `sidebar` в `frontend/src/locales/ru.json` (ключи пунктов меню).
- Создан `frontend/src/contexts/AuthContext.jsx` — роль определяется из URL-пути (`/user/*` → user, `/employee/*` → employee). Заглушка до появления JWT-auth, forward-compatible.
- Создан `frontend/src/components/Sidebar.jsx` + `Sidebar.css`:
  - Один переиспользуемый компонент для обеих ролей, набор пунктов формируется по роли из контекста.
  - Иконки из `lucide-react`: Settings / FileText / Pencil (user), Settings / Clock / LayoutList (employee).
  - Ширина по умолчанию 240px, регулируется перетаскиванием (невидимая зона захвата на правом крае, визуальная «ручка» — `border-right`), от 60px до 30vw.
  - Collapse/expand кнопкой: в свёрнутом состоянии — только иконки (60px), текст скрыт, tooltip на hover, логотип остаётся, зона захвата скрыта.
  - Активный пункт — акцентный цвет `--accent` и фон `--accent-bg`.
  - Тексты через i18n-ключи.
- Создан `frontend/src/components/Layout.jsx` + `Layout.css` — обёртка `<Sidebar /> + <Outlet />`, flex, контент адаптируется к ширине сайдбара.
- Обновлён `frontend/src/App.jsx` — все `/user/*` и `/employee/*` маршруты вложены под `Layout` с `AuthProvider`, дублирования нет.

## Затронутые файлы
- frontend/package.json (+lucide-react)
- frontend/package-lock.json
- frontend/src/locales/ru.json (+sidebar)
- frontend/src/contexts/AuthContext.jsx
- frontend/src/components/Sidebar.jsx
- frontend/src/components/Sidebar.css
- frontend/src/components/Layout.jsx
- frontend/src/components/Layout.css
- frontend/src/App.jsx
- openspec/TASKS.md (COMP-001 → done)

## Проверка
- Фронтенд-тестов в проекте нет (скриптов тестов в `package.json` нет). `npm run build` в `frontend/` — проходит без ошибок.

## Осталось / передаётся дальше
- AuthContext теперь (после AUTH-007) читает роль из `/api/auth/me`, а не из URL-пути — потребители менять не нужно (см. AUTH-007.md).
- Детальные маршруты с query-параметром `?menu={id}` (`/user/my?menu={id}`, `/employee/application?menu={id}`) сайдбар отдельно не выделяет — это выйдет с реализацией APP-005/EMP-005.

## Блокеры
- Нет.