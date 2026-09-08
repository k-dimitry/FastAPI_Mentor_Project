import pytest

from users.services import UserService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def service(db_session):
    """Создаёт экземпляр UserService с тестовой сессией."""
    return UserService(db_session)
