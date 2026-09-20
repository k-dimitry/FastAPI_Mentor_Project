from unittest.mock import AsyncMock

import pytest

from api.v1.users.dependencies import get_user_service
from main import app
from users.services import UserService

CORRECT_PASSWORD: str = 'StrongPass123!'


@pytest.fixture
def mock_auth_service():
    """Подменяет get_user_service на AsyncMock через dependency_overrides."""
    mock_service = AsyncMock(spec=UserService)

    app.dependency_overrides[get_user_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.pop(get_user_service, None)
