from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from api.v1.tasks.dependencies import get_task_service
from main import app
from tasks.services import TaskService


@pytest_asyncio.fixture
async def created_task(create_task_in_db, test_user):
    """Задача, принадлежащая test_user, с известными данными."""
    return await create_task_in_db(
        user_id=test_user.id,
        title='Original Task',
        description='Original description',
    )


@pytest_asyncio.fixture
async def tasks_for_user(create_task_in_db, test_user):
    """Три задачи с известными title/description для test_user."""
    task_1 = await create_task_in_db(
        user_id=test_user.id, title='Task 1', description='desc1'
    )
    task_2 = await create_task_in_db(
        user_id=test_user.id, title='Task 2', description=None
    )
    task_3 = await create_task_in_db(
        user_id=test_user.id, title='Task 3', description='desc3'
    )
    return {'task_1': task_1, 'task_2': task_2, 'task_3': task_3}


@pytest.fixture
def mock_task_service():
    """Подменяет get_task_service на AsyncMock через dependency_overrides."""
    mock_service = AsyncMock(spec=TaskService)

    app.dependency_overrides[get_task_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.pop(get_task_service, None)


@pytest_asyncio.fixture
async def other_user(create_user_in_db):
    """Второй обычный пользователь — для проверки изоляции."""
    return await create_user_in_db(
        username='otheruser',
        email='otheruser@example.com',
    )
