import uuid
from unittest.mock import ANY

import pytest
from fastapi import status
from httpx import AsyncClient


class TestUserRegister:
    @pytest.fixture
    async def registered_user(self, client: AsyncClient):
        """Регистрирует пользователя и возвращает его данные."""
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1995-01-01',
        }
        response = await client.post('/api/v1/users/register', json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        return response.json()

    async def test_register_success(self, client: AsyncClient):
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
        # Проверяем структуру и типы
        assert data == {
            'id': ANY,
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'birthdate': '1995-01-01',
            'created_at': ANY,
            'updated_at': ANY,
            'is_admin': False,
        }
        # id должен быть валидным UUID
        uuid.UUID(data['id'])

    async def test_register_duplicate(
        self, client: AsyncClient, registered_user
    ):
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
        # Проверяем, что detail содержит информацию о конфликте
        assert 'already exists' in response.json()['detail']

    @pytest.mark.parametrize(
        'password',
        [
            'weak',
            'short',
            '12345678',
            'nouppercase1!',
            'NOLOWERCASE1!',
            'NoNumber!',
            'NoSpecialChar1',
        ],
    )
    async def test_register_invalid_password(
        self, client: AsyncClient, password: str
    ):
        response = await client.post(
            '/api/v1/users/register',
            json={
                'username': 'user',
                'email': 'user@example.com',
                'first_name': 'User',
                'last_name': 'User',
                'password': password,
                'birthdate': '1995-01-01',
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        # Проверяем, что ошибка связана с полем password
        assert any(
            'password' in err['loc'] for err in response.json()['detail']
        )
