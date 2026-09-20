from datetime import date
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from api.v1.users.dependencies import get_user_service
from main import app
from users.services import UserService

CORRECT_PASSWORD: str = 'StrongPass123!'


@pytest_asyncio.fixture
async def registered_user(create_user_in_db):
    """Пользователь в БД, созданный для тестов регистрации."""
    return await create_user_in_db(
        username='newuser',
        email='newuser@example.com',
        password='StrongPass123!',
        first_name='New',
        last_name='User',
        birthdate=date(1995, 1, 1),
    )


@pytest.fixture
def mock_user_service():
    """Подменяет get_user_service на AsyncMock через dependency_overrides."""
    mock_service = AsyncMock(spec=UserService)

    async def _override() -> UserService:
        return mock_service

    app.dependency_overrides[get_user_service] = _override
    yield mock_service
    app.dependency_overrides.pop(get_user_service, None)
