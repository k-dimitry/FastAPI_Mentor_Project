import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common.security import create_access_token
from database import Base, get_db
from main import app
from tasks.models import Task
from users.models import User

# Тестовая БД (in-memory)
TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

TestSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    # Создаём таблицы перед тестом
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Удаляем таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user():
    async with TestSessionLocal() as session:
        user = User(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            hashed_password='hashed_password_placeholder',
            is_admin=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def admin_user():
    async with TestSessionLocal() as session:
        user = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            hashed_password='hashed_password_placeholder',
            is_admin=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
def user_token(test_user):
    return create_access_token({'sub': str(test_user.id)})


@pytest.fixture
def admin_token(admin_user):
    return create_access_token({'sub': str(admin_user.id)})
