from datetime import date

import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio
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
