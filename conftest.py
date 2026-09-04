import asyncio
from typing import AsyncGenerator, Optional
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from common.security import create_access_token, hash_password
from database import Base, get_db
from main import app
from tasks.models import Task
from users.models import User

# Тестовая БД: in-memory SQLite с общим кэшем для всех соединений
TEST_DATABASE_URL = (
    'sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true'
)
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)

TestSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Предоставляет сессию БД для прямых проверок."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def create_user_in_db(db_session: AsyncSession):
    async def _create_user(
        username: str = 'testuser',
        email: str = 'testuser@example.com',
        password: str = 'StrongPass123!',
        is_admin: bool = False,
        **kwargs,
    ) -> User:
        first_name = kwargs.pop('first_name', 'Test')
        last_name = kwargs.pop('last_name', 'User')
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            is_admin=is_admin,
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
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            is_done=is_done,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    return _create_task


@pytest_asyncio.fixture
async def task_for_user(create_task_in_db, test_user):
    return await create_task_in_db(user_id=test_user.id)
