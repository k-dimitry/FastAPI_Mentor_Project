import pytest

from tasks.services import TaskService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def service(db_session):
    """Создаёт TaskService с тестовой сессией."""
    return TaskService(db_session)
