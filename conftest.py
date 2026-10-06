import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from typing import AsyncGenerator, Optional

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from celery_app import celery_app
from common.security import create_access_token, hash_password
from config import settings
from database import Base, get_db
from main import app
from tasks.models import Task
from users.models import User


@dataclass(frozen=True)
class TestDatabase:
    async_url: URL
    sync_url: URL


def _app_database_names() -> set[str]:
    names: set[str] = set()
    app_url = make_url(str(settings.DATABASE_URL))
    if app_url.database:
        names.add(app_url.database)
    sync_url = make_url(settings.SYNC_DATABASE_URL)
    if sync_url.get_backend_name() == 'postgresql' and sync_url.database:
        names.add(sync_url.database)
    return names


def _resolve_async_url() -> URL:
    raw = os.environ.get('TEST_DATABASE_URL')
    if raw:
        return make_url(raw)
    app_url = make_url(str(settings.DATABASE_URL))
    if not app_url.database:
        raise RuntimeError('DATABASE_URL не содержит имя базы')
    return app_url.set(database=f'{app_url.database}_test')


def _resolve_sync_url(async_url: URL) -> URL:
    raw = os.environ.get('SYNC_TEST_DATABASE_URL')
    if raw:
        return make_url(raw)
    return async_url.set(drivername='postgresql+psycopg2')


def _build_test_database() -> TestDatabase:
    """Собирает и валидирует два URL для тестовой БД."""
    async_url = _resolve_async_url()
    sync_url = _resolve_sync_url(async_url)

    app_names = _app_database_names()
    for url in (async_url, sync_url):
        if url.database in app_names:
            raise RuntimeError(
                f'Тестовая база совпадает с рабочей: {url.database!r}. '
                'Нужна отдельная база.'
            )

    same_target = (
        async_url.host == sync_url.host
        and async_url.port == sync_url.port
        and async_url.database == sync_url.database
    )
    if not same_target:
        raise RuntimeError(
            'TEST_DATABASE_URL и SYNC_TEST_DATABASE_URL '
            'указывают на разные базы'
        )

    return TestDatabase(async_url=async_url, sync_url=sync_url)


def _ensure_database_exists(url: URL) -> None:
    """Создаёт тестовую базу, если её ещё нет."""
    name = url.database
    if not name:
        raise RuntimeError('URL тестовой базы не содержит имя базы')

    admin_url = url.set(drivername='postgresql+psycopg2', database='postgres')
    admin_engine = create_engine(
        admin_url.render_as_string(hide_password=False),
        isolation_level='AUTOCOMMIT',
        poolclass=NullPool,
    )
    try:
        quoted = admin_engine.dialect.identifier_preparer.quote(name)
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text('SELECT 1 FROM pg_database WHERE datname = :name'),
                {'name': name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE {quoted}'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope='session')
def test_database() -> TestDatabase:
    db = _build_test_database()
    _ensure_database_exists(db.sync_url)
    return db


@pytest.fixture(scope='session')
def sync_engine(test_database: TestDatabase):
    engine = create_engine(
        test_database.sync_url.render_as_string(hide_password=False),
        poolclass=NullPool,
        connect_args={'options': '-c timezone=UTC'},
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope='session')
def async_engine(test_database: TestDatabase):
    return create_async_engine(
        test_database.async_url.render_as_string(hide_password=False),
        echo=False,
        poolclass=NullPool,
        connect_args={'server_settings': {'timezone': 'UTC'}},
    )


@pytest.fixture(scope='session')
def session_factory(async_engine):
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture(scope='session')
def sync_session_factory(sync_engine):
    return sessionmaker(
        bind=sync_engine,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture(scope='session', autouse=True)
def setup_schema(sync_engine):
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield


@pytest.fixture(autouse=True)
def clean_tables(setup_schema, sync_engine):
    """Очищает таблицы до теста. Сессии открываются уже после TRUNCATE."""
    names = ', '.join(
        f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables)
    )
    with sync_engine.begin() as conn:
        conn.execute(text(f'TRUNCATE {names} RESTART IDENTITY CASCADE'))
    yield


@pytest_asyncio.fixture
async def client(clean_tables, session_factory):
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url='http://test',
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def db_session(clean_tables, session_factory) -> AsyncSession:
    """Предоставляет сессию БД для прямых проверок."""
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def create_user_in_db(db_session: AsyncSession):
    async def _create_user(
        username: str = 'testuser',
        email: str = 'testuser@example.com',
        password: str = 'StrongPass123!',
        is_admin: bool = False,
        birthdate: date | str | None = None,
        **kwargs,
    ) -> User:
        if isinstance(birthdate, str):
            birthdate = date.fromisoformat(birthdate)

        user = User(
            username=username,
            email=email,
            first_name=kwargs.pop('first_name', 'Test'),
            last_name=kwargs.pop('last_name', 'User'),
            hashed_password=hash_password(password),
            is_admin=is_admin,
            birthdate=birthdate,
            **kwargs,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


@pytest_asyncio.fixture
async def test_user(create_user_in_db):
    return await create_user_in_db()


@pytest_asyncio.fixture
async def admin_user(create_user_in_db):
    return await create_user_in_db(
        username='admin',
        email='admin@example.com',
        is_admin=True,
    )


@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token({'sub': str(test_user.id)})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token({'sub': str(admin_user.id)})


@pytest_asyncio.fixture
async def create_task_in_db(db_session: AsyncSession):
    async def _create_task(
        user_id,
        title: str = 'Test Task',
        description: Optional[str] = None,
        is_done: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            is_done=is_done,
        )
        if created_at is not None:
            task.created_at = created_at
        if updated_at is not None:
            task.updated_at = updated_at
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    return _create_task


@pytest_asyncio.fixture
async def task_for_user(create_task_in_db, test_user):
    return await create_task_in_db(user_id=test_user.id)


@pytest_asyncio.fixture
async def fake_redis(monkeypatch):
    """Заменяет common.redis_client._redis на in-memory FakeRedis."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr('common.redis_client._redis', fake, raising=False)
    yield fake
    await fake.aclose()


@pytest.fixture(autouse=True)
def celery_eager(monkeypatch, sync_session_factory):
    """Celery выполняется синхронно в той же Postgres, что и API-тесты."""
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    @contextmanager
    def _get_sync_session():
        session = sync_session_factory()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(
        'notifications.services.get_sync_session',
        _get_sync_session,
    )
    monkeypatch.setattr(
        'tasks.services.get_sync_session',
        _get_sync_session,
    )
    yield
