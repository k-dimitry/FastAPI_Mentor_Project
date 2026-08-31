import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        '/api/v1/users/register',
        json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1995-01-01',
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['username'] == 'newuser'
    assert data['email'] == 'newuser@example.com'
    assert 'id' in data
    assert 'password' not in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    # Первая регистрация
    await client.post(
        '/api/v1/users/register',
        json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1995-01-01',
        },
    )
    # Повторная с тем же username/email
    response = await client.post(
        '/api/v1/users/register',
        json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1995-01-01',
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_register_invalid_password(client: AsyncClient):
    response = await client.post(
        '/api/v1/users/register',
        json={
            'username': 'user',
            'email': 'user@example.com',
            'first_name': 'User',
            'last_name': 'User',
            'password': 'weak',
            'birthdate': '1995-01-01',
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
