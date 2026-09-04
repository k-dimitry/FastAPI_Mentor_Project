import pytest
from fastapi import status
from httpx import AsyncClient


class TestLogin:
    @pytest.fixture
    async def login_user(self, create_user_in_db):
        return await create_user_in_db(
            username='loginuser',
            email='loginuser@example.com',
            password='StrongPass123!',
            first_name='Login',
            last_name='User',
        )

    async def test_login_success(self, client: AsyncClient, login_user):
        response = await client.post(
            '/api/v1/auth/login',
            json={
                'username_or_email': 'loginuser',
                'password': 'StrongPass123!',
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'

    async def test_login_wrong_password(self, client: AsyncClient, login_user):
        response = await client.post(
            '/api/v1/auth/login',
            json={
                'username_or_email': 'loginuser',
                'password': 'WrongPass123!',
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Уточните сообщение об ошибке в вашем эндпоинте
        assert response.json() == {'detail': 'Invalid credentials'}

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            '/api/v1/auth/login',
            json={'username_or_email': 'ghost', 'password': 'Whatever123!'},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}
