# FastAPI Mentor Project

Учебный REST API для управления задачами с JWT-аутентификацией, ролевой моделью, кэшем в Redis и rate limiting. Деплой через GitHub Actions + Docker Compose на VPS.

[![CI/CD](https://github.com/k-dimitry/FastAPI_Mentor_Project/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/k-dimitry/FastAPI_Mentor_Project/actions/workflows/ci-cd.yml)
[![Coverage](./coverage.svg)](./coverage.svg)

**Live API:** https://fastapi-project.hopto.org/docs

## Стек

- **Python 3.12** · **FastAPI** · **Pydantic v2** · **SQLAlchemy 2 (async)** · **Alembic**
- **PostgreSQL 16** — основная БД (dev + prod)
- **Redis 7** — кэш списка задач + счётчики rate limit
- **Gunicorn + UvicornWorker** — 4 воркера
- **Docker / Docker Compose** — упаковка и запуск
- **pytest + httpx + fakeredis + time-machine** — тесты
- **GitHub Actions** — CI/CD (тесты → GHCR → SSH-деплой)
- **Nginx + Let's Encrypt** — reverse proxy и HTTPS

## Возможности

- Регистрация, логин (JWT, OAuth2 Password Bearer), ролевая модель (`is_admin`)
- CRUD задач с изоляцией данных по владельцу
- Расширенный список задач: фильтр по статусу, диапазону дат, поиск по подстроке, сортировка, пагинация
- Статистика: `total`, `by-day`, `active-users`, `dashboard`
- Кэширование `GET /tasks/` в Redis и сброс кэша при изменении состояния задач
- Rate limit: 60 запросов / 60 секунд на user_id (или IP для анонимных)
- Логирование запросов с маскировкой чувствительных данных (пароли, токены)

## Быстрый старт (Docker)

```bash
git clone git@github.com:k-dimitry/FastAPI_Mentor_Project.git
cd FastAPI_Mentor_Project
cp .env.example .env
# при необходимости отредактировать .env

docker compose up -d
docker compose run --rm migrations
```
API: http://localhost:8080/docs

## Локальная разработка

```bash
uv sync                                     # создать .venv + установить зависимости
docker compose up -d db redis               # поднять только БД и Redis
uv run alembic upgrade head                 # применить миграции
uv run uvicorn main:app --reload            # запуск с автоперезагрузкой
```
## Тесты

```bash
uv run pytest -q                            # все тесты
uv run pytest --cov=./ --cov-report=term-missing
```

## Структура
```text
api/v1/         — FastAPI-роутеры, схемы запросов/ответов
  auth/         — логин, OAuth2-токен, зависимости (get_current_user, require_admin)
  users/        — регистрация, профиль
  tasks/        — CRUD, статистика, дашборд
common/         — security, cache, redis_client, middleware, pagination, mixins
tasks/          — DTO, модели, сервис, специфичный кэш
users/          — DTO, модели, сервис, permissions
alembic/        — миграции БД
```