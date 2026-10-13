import os

import pytest
from fastapi import Request, status
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import gunicorn_conf
from common.middleware import _get_rate_limit_identifier
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

    async def test_window_has_ttl(self, client, fake_redis, user_token):
        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        assert response.status_code == status.HTTP_200_OK

        keys = await fake_redis.keys('rl:*')
        assert len(keys) == 1
        ttl = await fake_redis.ttl(keys[0])
        assert 0 < ttl <= settings.RATE_LIMIT_T

    async def test_key_without_ttl_gets_expire(
        self, client, fake_redis, user_token
    ):
        await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        key = (await fake_redis.keys('rl:*'))[0]
        await fake_redis.persist(key)
        assert await fake_redis.ttl(key) == -1

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert int(await fake_redis.get(key)) == 2
        ttl = await fake_redis.ttl(key)
        assert 0 < ttl <= settings.RATE_LIMIT_T

    async def test_existing_ttl_is_not_reset(
        self, client, fake_redis, user_token
    ):
        await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        key = (await fake_redis.keys('rl:*'))[0]
        await fake_redis.expire(key, 10)

        await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        ttl = await fake_redis.ttl(key)
        assert 0 < ttl <= 10
        assert int(await fake_redis.get(key)) == 2


def _trusted_peer() -> str:
    first = gunicorn_conf.forwarded_allow_ips.split(',')[0].strip()
    if first == '*' or '/' in first:
        pytest.skip('FORWARDED_ALLOW_IPS is not a single host')
    return first


async def _rate_limit_id(peer: str, forwarded_for: str) -> str:
    seen = {}

    async def app(scope, receive, send):
        request = Request(scope)
        seen['identifier'] = _get_rate_limit_identifier(request)

    middleware = ProxyHeadersMiddleware(
        app,
        trusted_hosts=gunicorn_conf.forwarded_allow_ips,
    )
    scope = {
        'type': 'http',
        'client': (peer, 12345),
        'headers': [(b'x-forwarded-for', forwarded_for.encode())],
    }
    await middleware(scope, None, None)
    return seen['identifier']


class TestForwardedClientIp:
    def test_forwarded_allow_ips_defaults_to_loopback(self):
        assert gunicorn_conf.forwarded_allow_ips == os.getenv(
            'FORWARDED_ALLOW_IPS', '127.0.0.1'
        )
        assert gunicorn_conf.forwarded_allow_ips != '*'

    async def test_untrusted_peer_ignores_spoofed_forwarded_for(self):
        peer = '203.0.113.8'
        if peer == _trusted_peer():
            peer = '203.0.113.9'

        first = await _rate_limit_id(peer, '198.51.100.1')
        second = await _rate_limit_id(peer, '198.51.100.2')

        assert first == f'ip:{peer}'
        assert second == first

    async def test_trusted_proxy_uses_forwarded_for(self):
        identifier = await _rate_limit_id(_trusted_peer(), '198.51.100.9')

        assert identifier == 'ip:198.51.100.9'
