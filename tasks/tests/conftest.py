import pytest
import pytest_asyncio

from tasks.dto import TaskCreateDTO
from tasks.services import TaskService

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def service(db_session):
    """Создаёт TaskService с тестовой сессией БД."""
    return TaskService(db_session)


@pytest_asyncio.fixture
async def user(create_user_in_db):
    """Пользователь-владелец задач не админ)."""
    return await create_user_in_db(
        username='svc_user',
        email='svc@example.com',
    )


@pytest_asyncio.fixture
async def other_user(create_user_in_db):
    """Второй пользователь для проверки изоляции."""
    return await create_user_in_db(
        username='other_user',
        email='other@example.com',
    )


@pytest_asyncio.fixture
async def created_task(service, user):
    """Задача, принадлежащая user, созданная через сервис."""
    return await service.create_task(
        TaskCreateDTO(title='Original', description='original desc'),
        user_id=user.id,
    )
