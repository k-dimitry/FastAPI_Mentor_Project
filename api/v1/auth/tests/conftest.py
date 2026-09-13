import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def login_user(create_user_in_db):
    """Пользователь с известным паролем для тестов логина."""
    return await create_user_in_db(
        username='loginuser',
        email='loginuser@example.com',
        password='StrongPass123!',
        first_name='Login',
        last_name='User',
    )
