# FastAPI Mentor Project

Учебный REST API для задач: JWT, роли, кэш и rate limit в Redis, фоновые задачи в Celery. CI: линт и тесты, образ в GHCR, деплой на VPS.

[![CI/CD](https://github.com/k-dimitry/FastAPI_Mentor_Project/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/k-dimitry/FastAPI_Mentor_Project/actions/workflows/ci-cd.yml)
[![Coverage](./coverage.svg)](./coverage.svg)

**URL:** https://fastapi-project.hopto.org/docs

## Стек

Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, PostgreSQL 16, Redis 7, Celery, Gunicorn + Uvicorn, Docker Compose, uv, pytest, GitHub Actions.

## Возможности

- Регистрация и логин (JWT), роль `is_admin` читается из базы на каждом запросе
- CRUD задач с изоляцией по владельцу; список с фильтром, поиском, сортировкой и пагинацией
- `GET /api/v1/tasks/stats/total` и `/by-day` всегда по текущему пользователю, в том числе для админа
- `GET /api/v1/tasks/dashboard`: админ видит все задачи, остальные — свои
- Кэш `GET /api/v1/tasks/` в Redis и rate limit 60 запросов / 60 секунд (значения в `.env`)
- Celery: welcome-уведомление при регистрации, ночная очистка старых выполненных задач, снимок в `daily_stats`, ручной запуск очистки админом (`POST /api/v1/admin/cleanup`)

Контракт API — в `/docs`.

## Запуск

Переменные — в [`.env.example`](.env.example). Redis: `/0` — кэш и rate limit, `/1` — брокер Celery, `/2` — результаты задач.

### Docker

```bash
cp .env.example .env
# при необходимости сменить JWT_SECRET_KEY

docker compose up -d
```

Миграции применяются сами. API: http://localhost:8080/docs

Поднимаются API, Celery worker, beat, PostgreSQL и Redis.

### Локально

В `.env` для процессов на хосте замените `redis://redis` на `redis://localhost` (`REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`). `DATABASE_URL` в примере уже указывает на localhost.

```bash
uv sync
docker compose up -d db redis
uv run alembic upgrade head
uv run uvicorn main:app --reload
```

API: http://localhost:8000/docs

Worker и beat нужны только для фоновых задач: `uv run celery -A celery_app:celery_app worker` и `uv run celery -A celery_app:celery_app beat`.

## Первый админ

Регистрация всегда создаёт пользователя с `is_admin = false`. Роль выдаётся обновлением строки в Postgres (`POSTGRES_USER` и `POSTGRES_DB` из `.env`; в примере это `user` и `mydb`):

```bash
docker compose exec db psql -U user -d mydb \
  -c "UPDATE users SET is_admin = true WHERE username = 'имя';"
```

Роль читается из базы на каждом запросе, поэтому следующий запрос уже идёт с правами админа.

## Тесты

Нужен поднятый Postgres: `docker compose up -d db`. Тесты пишут в отдельную базу `{db}_test` (`mydb` → `mydb_test`) и рабочую базу не очищают.

```bash
uv run pytest -q
uv run pytest --cov=./ --cov-report=term-missing
```

## Структура

```text
api/             — роутеры и схемы
common/          — security, кэш, Redis, middleware
tasks/           — модели, сервис и кэш задач
users/           — модели, сервис, права
notifications/   — welcome-уведомления и Celery-задачи
alembic/         — миграции
main.py          — приложение FastAPI
celery_app.py    — worker и beat
config.py        — настройки из .env
```
