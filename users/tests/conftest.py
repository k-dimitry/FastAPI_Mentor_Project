from datetime import date

import pytest
import pytest_asyncio

from users.dto import UserCreateDTO
from users.services import UserService

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def service(db_session):
    """Создаёт экземпляр UserService с тестовой сессией."""
    return UserService(db_session)


@pytest_asyncio.fixture
async def existing_user(service):
    """Создаёт пользователя через сервис и возвращает его DTO."""
    return await service.create_user(
        UserCreateDTO(
            username='existing',
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            password='Str0ngPass!',
            birthdate=date(1990, 5, 15),
        )
    )
