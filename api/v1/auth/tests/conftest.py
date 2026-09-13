import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio

CORRECT_PASSWORD: str = 'StrongPass123!'

@pytest_asyncio.fixture
async def login_user(create_user_in_db):
    """Пользователь с известным паролем для тестов логина."""
    return await create_user_in_db(
        username='loginuser',
        email='loginuser@example.com',
        password=CORRECT_PASSWORD,
        first_name='Login',
        last_name='User',
    )
