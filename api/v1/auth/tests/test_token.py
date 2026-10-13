from datetime import datetime, timedelta, timezone

import pytest
import time_machine
from fastapi import status
from httpx import AsyncClient
from jose import jwt

from api.v1.auth.tests.conftest import CORRECT_PASSWORD
from common.security import decode_access_token
from config import settings


class TestTokenSuccess:
    @pytest.mark.parametrize(
        'credential', ['tokenuser', 'token@example.com']
    )
    @time_machine.travel(
        datetime(2026, 9, 15, 10, 30, tzinfo=timezone.utc), tick=False
    )
    async def test_token_success(
        self, client: AsyncClient, create_user_in_db, credential: str
    ):
        fixed_dt = datetime(2026, 9, 15, 10, 30, tzinfo=timezone.utc)
        user = await create_user_in_db(
            username='tokenuser',
            email='token@example.com',
            password=CORRECT_PASSWORD,
        )
        expected_exp = int(
            (
                fixed_dt + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            ).timestamp()
        )

        response = await client.post(
            '/api/v1/auth/token',
            data={'username': credential, 'password': CORRECT_PASSWORD},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == {'access_token', 'token_type'}
        assert data['token_type'] == 'bearer'

        header = jwt.get_unverified_header(data['access_token'])
        assert header == {'alg': settings.JWT_ALGORITHM, 'typ': 'JWT'}

        decoded = decode_access_token(data['access_token'])
        assert decoded is not None
        assert decoded['sub'] == str(user.id)
        assert decoded['exp'] == expected_exp


class TestTokenFailure:
    async def test_token_wrong_password(
        self, client: AsyncClient, create_user_in_db
    ):
        await create_user_in_db(
            username='tokenuser',
            email='token@example.com',
            password=CORRECT_PASSWORD,
        )

        response = await client.post(
            '/api/v1/auth/token',
            data={'username': 'tokenuser', 'password': 'WrongPass123!'},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            'detail': 'Incorrect username or password'
        }
        assert response.headers['www-authenticate'] == 'Bearer'

    async def test_token_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            '/api/v1/auth/token',
            data={'username': 'ghost', 'password': CORRECT_PASSWORD},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            'detail': 'Incorrect username or password'
        }
        assert response.headers['www-authenticate'] == 'Bearer'

    async def test_token_missing_password(self, client: AsyncClient):
        response = await client.post(
            '/api/v1/auth/token',
            data={'username': 'tokenuser'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        body = response.json()
        assert body['detail'][0]['loc'] == ['body', 'password']
        assert body['detail'][0]['type'] == 'missing'
