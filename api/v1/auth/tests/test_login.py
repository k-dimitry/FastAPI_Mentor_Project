import pytest
from fastapi import status
from httpx import AsyncClient

from api.v1.auth.tests.conftest import CORRECT_PASSWORD
from common.security import decode_access_token


class TestLoginSuccess:
    @pytest.mark.parametrize('login_field', ['username', 'email'])
    async def test_login_success(
        self, client: AsyncClient, login_user, login_field
    ):
        credential = getattr(login_user, login_field)
        password = CORRECT_PASSWORD

        response = await client.post(
            '/api/v1/auth/login',
            json={
                'username_or_email': credential,
                'password': password,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert set(data.keys()) == {'access_token', 'token_type'}
        assert data['token_type'] == 'bearer'
        assert isinstance(data['access_token'], str)
        assert len(data['access_token']) > 0

        payload = decode_access_token(data['access_token'])
        assert payload is not None
        assert payload['sub'] == str(login_user.id)
        assert 'exp' in payload


class TestLoginFailure:
    async def test_login_wrong_password(self, client: AsyncClient, login_user):
        payload = {
            'username_or_email': login_user.username,
            'password': 'WrongPass123!',
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}

    async def test_login_nonexistent_user(self, client: AsyncClient):
        payload = {
            'username_or_email': 'ghost',
            'password': 'Whatever123!',
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}

    async def test_login_wrong_username_correct_password(
        self, client: AsyncClient, login_user
    ):
        payload = {
            'username_or_email': 'nonexistent',
            'password': CORRECT_PASSWORD,
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}
