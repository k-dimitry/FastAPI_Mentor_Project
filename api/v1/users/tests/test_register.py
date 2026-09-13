import uuid
from datetime import datetime, timezone

import pytest
import time_machine
from fastapi import status
from httpx import AsyncClient

from conftest import as_naive_utc


class TestUserRegisterSuccess:
    @time_machine.travel(
        datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc),
        tick=False,
    )
    async def test_register_success(self, client: AsyncClient):
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
        data = response.json()

        assert data == {
            'id': data['id'],
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'birthdate': '1995-01-01',
            'created_at': data['created_at'],
            'updated_at': data['updated_at'],
            'is_admin': False,
        }

        user_id = uuid.UUID(data['id'])
        assert isinstance(user_id, uuid.UUID)

        expected_naive = datetime(2026, 8, 30, 12, 30)

        created_at = datetime.fromisoformat(
            data['created_at'].replace('Z', '+00:00')
        )
        updated_at = datetime.fromisoformat(
            data['updated_at'].replace('Z', '+00:00')
        )
        assert as_naive_utc(created_at) == expected_naive
        assert as_naive_utc(updated_at) == expected_naive

    async def test_register_without_birthdate(self, client: AsyncClient):
        payload = {
            'username': 'nobirth',
            'email': 'nobirth@example.com',
            'first_name': 'No',
            'last_name': 'Birthdate',
            'password': 'StrongPass123!',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['birthdate'] is None


class TestUserRegisterDuplicate:
    @pytest.mark.parametrize(
        'username,email,expect_detail_fragment',
        [
            ('newuser', 'different@example.com', 'newuser'),
            ('different', 'newuser@example.com', 'newuser@example.com'),
            ('newuser', 'newuser@example.com', 'newuser'),
        ],
    )
    async def test_register_duplicate(
        self,
        client: AsyncClient,
        registered_user,
        username,
        email,
        expect_detail_fragment,
    ):
        payload = {
            'username': username,
            'email': email,
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1995-01-01',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT
        body = response.json()
        assert 'detail' in body
        assert 'already exists' in body['detail']


class TestUserRegisterValidation:
    @pytest.mark.parametrize(
        'password',
        [
            'weak',
            'short',
            '12345678',
            'nouppercase1!',
            'NOLOWERCASE1!',
            'NoNumber!',
            'NoSpecialChar111111',
        ],
    )
    async def test_register_invalid_password(
        self, client: AsyncClient, password: str
    ):
        payload = {
            'username': 'user',
            'email': 'user@example.com',
            'first_name': 'User',
            'last_name': 'User',
            'password': password,
            'birthdate': '1995-01-01',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        body = response.json()
        assert 'detail' in body
        assert any('password' in err['loc'] for err in body['detail'])

    @pytest.mark.parametrize(
        'field,value',
        [
            ('username', 'ab'),
            ('email', 'not-an-email'),
            ('first_name', ''),
            ('last_name', ''),
        ],
    )
    async def test_register_invalid_fields(
        self, client: AsyncClient, field: str, value: str
    ):
        payload = {
            'username': 'user',
            'email': 'user@example.com',
            'first_name': 'User',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'birthdate': '1995-01-01',
            field: value,
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        body = response.json()
        assert any(field in err['loc'] for err in body['detail'])
