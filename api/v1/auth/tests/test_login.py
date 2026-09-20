from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import time_machine
from fastapi import status
from httpx import AsyncClient
from jose import jwt

from api.v1.auth.tests.conftest import CORRECT_PASSWORD
from common.security import decode_access_token
from config import settings
from users.dto import UserResponseDTO


class TestLoginSuccess:
    @pytest.mark.parametrize(
        'credential', ['loginuser', 'loginuser@example.com']
    )
    @time_machine.travel(
        datetime(2026, 9, 15, 10, 30, tzinfo=timezone.utc), tick=False
    )
    async def test_login_success(
        self, client: AsyncClient, mock_auth_service, credential: str
    ):
        fixed_dt = datetime(2026, 9, 15, 10, 30, tzinfo=timezone.utc)
        fixed_user_id = UUID('11111111-1111-1111-1111-111111111111')

        mock_auth_service.authenticate_user.return_value = UserResponseDTO(
            id=fixed_user_id,
            username='loginuser',
            email='loginuser@example.com',
            first_name='Login',
            last_name='User',
            birthdate=None,
            created_at=fixed_dt,
            updated_at=fixed_dt,
            is_admin=False,
        )

        expected_exp = int(
            (
                fixed_dt
                + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            ).timestamp()
        )

        payload = {
            'username_or_email': credential,
            'password': CORRECT_PASSWORD,
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert set(data.keys()) == {'access_token', 'token_type'}
        assert data['token_type'] == 'bearer'

        parts = data['access_token'].split('.')
        assert len(parts) == 3

        header = jwt.get_unverified_header(data['access_token'])
        assert header == {'alg': settings.JWT_ALGORITHM, 'typ': 'JWT'}

        decoded = decode_access_token(data['access_token'])
        assert decoded is not None
        assert set(decoded.keys()) == {'sub', 'exp'}
        assert decoded['sub'] == str(fixed_user_id)
        assert decoded['exp'] == expected_exp

        mock_auth_service.authenticate_user.assert_called_once_with(
            credential, CORRECT_PASSWORD
        )


class TestLoginFailure:
    async def test_login_wrong_password(
        self, client: AsyncClient, mock_auth_service
    ):
        mock_auth_service.authenticate_user.return_value = None
        payload = {
            'username_or_email': 'loginuser',
            'password': 'WrongPass123!',
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}
        mock_auth_service.authenticate_user.assert_called_once_with(
            'loginuser', 'WrongPass123!'
        )

    async def test_login_nonexistent_user(
        self, client: AsyncClient, mock_auth_service
    ):
        mock_auth_service.authenticate_user.return_value = None
        payload = {
            'username_or_email': 'ghost',
            'password': 'Whatever123!',
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}
        mock_auth_service.authenticate_user.assert_called_once_with(
            'ghost', 'Whatever123!'
        )

    async def test_login_wrong_username_correct_password(
        self, client: AsyncClient, mock_auth_service
    ):
        mock_auth_service.authenticate_user.return_value = None
        payload = {
            'username_or_email': 'nonexistent',
            'password': CORRECT_PASSWORD,
        }

        response = await client.post('/api/v1/auth/login', json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid credentials'}
        mock_auth_service.authenticate_user.assert_called_once_with(
            'nonexistent', CORRECT_PASSWORD
        )