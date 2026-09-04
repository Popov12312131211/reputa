# Reputa

Сервис альтернативного кредитного скоринга для людей без официальной кредитной истории — студентов, самозанятых, фрилансеров. Оценка благонадёжности (0–100) на основе банковской выписки и публичного Telegram-канала.

## Стек

- **Фронтенд:** React + Vite + Nginx
- **Бэкенд:** Python + FastAPI
- **БД:** PostgreSQL 16
- **Авторизация:** JWT в httpOnly cookie

## Требования

- [Docker](https://www.docker.com/) ≥ 20
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2

## Запуск

### Быстрый старт (Docker)

```bash
docker compose up --build -d
```

Эта команда соберёт и запустит все сервисы:

| Сервис | Описание | URL |
|---|---|---|
| **frontend** | React-приложение (Nginx) | http://localhost |
| **backend** | FastAPI-сервер | http://localhost:8000 |
| **db** | PostgreSQL 16 | localhost:5432 |

Миграции БД применяются автоматически при старте backend.

### Остановка

```bash
docker compose down
```

Для полного удаления данных (включая БД):

```bash
docker compose down -v
```

### Логи

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## Локальная разработка (без Docker для backend/frontend)

### 1. Поднять базу данных

```bash
docker compose up db -d
```

### 2. Бэкенд

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Бэкенд стартует на `http://127.0.0.1:8000`.

### 3. Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Фронтенд стартует на `http://localhost:5173`, запросы к `/api` проксируются на бэкенд.

## Структура проекта

```
reputa/
├── backend/          # FastAPI-приложение
│   ├── app/          # Модули API
│   ├── alembic/      # Миграции
│   └── tests/        # Тесты
├── frontend/         # React-приложение
│   └── src/
│       ├── components/
│       └── locales/  # Переводы (i18n)
├── frontend-temp/    # Макеты вёрстки
└── openspec/         # Спецификации продукта
```
