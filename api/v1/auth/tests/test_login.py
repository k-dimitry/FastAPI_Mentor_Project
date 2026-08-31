import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Регистрируем пользователя
    await client.post(
        '/api/v1/users/register',
        json={
            'username': 'loginuser',
            'email': 'loginuser@example.com',
            'first_name': 'Login',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1990-01-01',
        },
    )
    # Логинимся
    response = await client.post(
        '/api/v1/auth/login',
        json={'username_or_email': 'loginuser', 'password': 'StrongPass123!'},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    # Регистрируем пользователя
    await client.post(
        '/api/v1/users/register',
        json={
            'username': 'loginuser',
            'email': 'loginuser@example.com',
            'first_name': 'Login',
            'last_name': 'User',
            'password': 'StrongPass123!',
        },
    )
    # Неверный пароль
    response = await client.post(
        '/api/v1/auth/login',
        json={'username_or_email': 'loginuser', 'password': 'WrongPass123!'},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        '/api/v1/auth/login',
        json={'username_or_email': 'ghost', 'password': 'Whatever123!'},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
