# Telegram Anonymous Relay Bot (Polling + Postgres)

Минималистичный production-ready бот на `aiogram v3`, который позволяет анонимизированно общаться через личку с ботом.

## Возможности

- Только личные сообщения с ботом (группы/каналы игнорируются).
- Long polling + параллельный HTTP health server.
- Модерация доступа админом: `pending -> setup -> active`, плюс `banned`.
- Анонимная рассылка всем active-пользователям (кроме отправителя).
- Поддержка:
  - `text`
  - `photo`
  - `video`
  - `document`
  - `media_group` (альбомы, буфер 1.5 сек)
- Reply через стандартный Telegram reply с кодами `M0001...` и обязательной цитатой.
- PostgreSQL (Supabase free tier) через `DATABASE_URL`.
- Docker-ready (`Dockerfile`, `docker-compose.yml`).

## Стек

- Python 3.11+
- aiogram 3
- asyncpg
- FastAPI + uvicorn
- python-dotenv

## Структура

- `app/main.py` — параллельный старт polling + `/health`.
- `app/config.py` — загрузка `.env`.
- `app/db.py` — asyncpg pool и инициализация Postgres.
- `app/repositories/*` — слой данных users/messages.
- `app/services/broadcast.py` — рассылка и формат сообщений.
- `app/services/media_group.py` — буферизация альбомов.
- `app/handlers/*` — команды и логика чата.
- `app/utils/parsing.py` — извлечение кодов и цитат.
- `sql/init.sql` — SQL-инициализация таблиц.

## Конфигурация

1. Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

2. Заполните:

```env
BOT_TOKEN=ваш_токен_бота
ADMIN_ID=ваш_telegram_id
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
PORT=10000
LOG_LEVEL=INFO
```

## Локальный запуск

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Запуск в Docker

```bash
docker compose up --build
```

Бот запускается в одном async-процессе: Telegram polling + HTTP сервер с `GET /health`.

## Команды

### Пользователь

- `/start`
- `/whoami`

### Админ

- `/approve <telegram_id>`
- `/reject <telegram_id>`
- `/ban <telegram_id>`
- `/list`

Также для новых заявок админ получает inline-кнопки `Approve / Reject`.

## Формат сообщений

Обычное сообщение:

```text
M0005 | [CLIENT] IvanK
Текст сообщения
```

Reply:

```text
M0008 ↪ M0005 | [VENDOR] Dev1
Цитата: "первые 200 символов оригинала"
Ответный текст
```

## Деплой бесплатно

### Railway

- Создайте сервис из репозитория.
- Добавьте переменные окружения `BOT_TOKEN`, `ADMIN_ID`, `DATABASE_URL`, `PORT`.
- Команда запуска: `python -m app.main`.

### Fly.io

- Создайте `fly app`.
- Задайте secrets: `fly secrets set BOT_TOKEN=... ADMIN_ID=... DATABASE_URL=...`.
- Убедитесь, что выставлен `PORT`.
- Запуск контейнера из `Dockerfile`.

### Render

- Создайте Web service (нужен внешний URL для `/health`).
- Build command: `pip install -r requirements.txt`.
- Start command: `python -m app.main`.
- Добавьте env vars `BOT_TOKEN`, `ADMIN_ID`, `DATABASE_URL`, `PORT`.

#### Anti-sleep для Render Free

- Настройте внешний пинг через UptimeRobot (или аналог).
- Интервал пинга: каждые `10-14 минут`.
- URL: `https://your-render-url/health`.
- Внутренний cron/timer внутри приложения не нужен: внешний мониторинг надежнее и проще.

### VPS / локальный сервер

- Установите Python 3.11+ или Docker.
- Запустите как systemd service или через `docker compose up -d`.

## Проверка сценариев

1. Новый пользователь: `/start` -> у админа заявка с кнопками.
2. Approve -> пользователь проходит setup (псевдоним + сторона).
3. Active-пользователь отправляет text/media.
4. Другой active-пользователь отвечает через Telegram reply.
5. Проверка album (несколько фото/видео/документов одним медиа-групп сообщением).

## Важно

- Webhook не используется.
- Endpoint `GET /health` возвращает `200` и `{"status": "ok"}`.
- Данные хранятся только во внешнем Postgres (без локальных DB-файлов).
