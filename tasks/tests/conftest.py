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


@pytest_asyncio.fixture
async def five_tasks(service, user):
    """Пять задач для user: Task 0 .. Task 4 (created_at ≈ now)."""
    tasks = []
    for i in range(5):
        task = await service.create_task(
            TaskCreateDTO(title=f'Task {i}'), user_id=user.id
        )
        tasks.append(task)
    return tasks


@pytest_asyncio.fixture
async def tasks_with_mixed_done(service, user):
    """Две задачи для user: одна is_done=True, одна is_done=False."""
    done = await service.create_task(
        TaskCreateDTO(title='Done', is_done=True), user_id=user.id
    )
    not_done = await service.create_task(
        TaskCreateDTO(title='Not Done', is_done=False), user_id=user.id
    )
    return {'done': done, 'not_done': not_done}
