import pytest
from fastapi import status

from config import settings


class TestRateLimit:
    @pytest.fixture(autouse=True)
    def small_limit(self, monkeypatch):
        monkeypatch.setattr(settings, 'RATE_LIMIT_N', 3)
        monkeypatch.setattr(settings, 'RATE_LIMIT_T', 60)

    async def test_under_limit(self, client, fake_redis, user_token):
        for _ in range(3):
            response = await client.get(
                '/api/v1/tasks/',
                headers={'Authorization': f'Bearer {user_token}'},
            )
            assert response.status_code == status.HTTP_200_OK

    async def test_over_limit_returns_429(self, client, fake_redis, user_token):
        for _ in range(3):
            await client.get(
                '/api/v1/tasks/',
                headers={'Authorization': f'Bearer {user_token}'},
            )

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.json() == {
            'detail': 'Too many requests',
            'limit': 3,
            'window': 60,
        }
        assert 'retry-after' in response.headers
        assert int(response.headers['retry-after']) > 0

    async def test_different_users_independent(
        self, client, fake_redis, user_token, admin_token
    ):
        for _ in range(3):
            await client.get(
                '/api/v1/tasks/',
                headers={'Authorization': f'Bearer {user_token}'},
            )

        exhausted = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        assert exhausted.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        other_user_response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {admin_token}'},
        )
        assert other_user_response.status_code == status.HTTP_200_OK

    async def test_anonymous_limited_by_ip(self, client, fake_redis):

        for _ in range(3):
            response = await client.get('/api/v1/tasks/')
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.get('/api/v1/tasks/')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    async def test_health_and_root_not_limited(self, client, fake_redis):
        for _ in range(10):
            r1 = await client.get('/health')
            r2 = await client.get('/')
            assert r1.status_code == status.HTTP_200_OK
            assert r2.status_code == status.HTTP_200_OK

        response = await client.get('/api/v1/tasks/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_redis_unavailable_skips_limit(
        self, client, monkeypatch, user_token
    ):
        monkeypatch.setattr('common.redis_client._redis', None)

        for _ in range(10):
            response = await client.get(
                '/api/v1/tasks/',
                headers={'Authorization': f'Bearer {user_token}'},
            )
            assert response.status_code == status.HTTP_200_OK
