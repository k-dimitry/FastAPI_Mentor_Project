import json
import logging
from time import perf_counter

from fastapi import Request, status
from fastapi.concurrency import iterate_in_threadpool
from fastapi.responses import JSONResponse

from common.redis_client import get_redis
from common.security import decode_access_token
from config import settings

logger = logging.getLogger('app')

SENSITIVE_FIELDS: set[str] = {
    'password',
    'token',
    'secret',
    'authorization',
    'hashed_password',
    'access_token',
    'refresh_token',
    'api_key',
}


def _is_sensitive_key(key: str) -> bool:
    """Проверяет, содержит ли ключ чувствительные подстроки."""
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS)


def _mask_sensitive_data(data):
    """Рекурсивно маскирует чувствительные данные в JSON-подобных структурах."""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if _is_sensitive_key(key):
                masked[key] = '***'
            else:
                masked[key] = _mask_sensitive_data(value)
        return masked
    elif isinstance(data, list):
        return [_mask_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        if '=' in data and ('&' in data or data.startswith('grant_type=')):
            pairs = data.split('&')
            masked_pairs = []
            for pair in pairs:
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    if _is_sensitive_key(k):
                        masked_pairs.append(f'{k}=***')
                    else:
                        masked_pairs.append(pair)
                else:
                    masked_pairs.append(pair)
            return '&'.join(masked_pairs)
    return data


def _safe_json_loads(body: bytes):
    try:
        return json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body.decode('utf-8', errors='replace')


def _get_rate_limit_identifier(request: Request) -> str:
    """Возвращает идентификатор для rate limit: user_id (из JWT) или IP."""
    auth = request.headers.get('authorization', '')
    if auth.lower().startswith('bearer '):
        token = auth[7:]
        payload = decode_access_token(token)
        if payload and (sub := payload.get('sub')):
            return f'user:{sub}'

    host = request.client.host if request.client else 'unknown'
    return f'ip:{host}'


async def rate_limit(request: Request, call_next):
    """Ограничивает число запросов с одного идентификатора (fixed window)."""
    if not request.url.path.startswith('/api/'):
        return await call_next(request)

    redis = get_redis()
    if redis is None:
        return await call_next(request)

    identifier = _get_rate_limit_identifier(request)
    key = f'rl:{identifier}'

    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, settings.RATE_LIMIT_T)
            ttl = settings.RATE_LIMIT_T
        else:
            ttl = await redis.ttl(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning('Rate limit check failed for %s: %s', identifier, exc)
        return await call_next(request)

    if count > settings.RATE_LIMIT_N:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                'detail': 'Too many requests',
                'limit': settings.RATE_LIMIT_N,
                'window': settings.RATE_LIMIT_T,
            },
            headers={
                'Retry-After': str(ttl if ttl > 0 else settings.RATE_LIMIT_T),
            },
        )

    return await call_next(request)


async def log_requests(request: Request, call_next):
    start_time = perf_counter()

    request_body = await request.body()

    async def receive():
        return {'type': 'http.request', 'body': request_body}

    request._receive = receive

    if request_body:
        parsed = _safe_json_loads(request_body)
        masked = _mask_sensitive_data(parsed)
        logger.debug(f'Request body: {masked}')

    response = await call_next(request)

    process_time = perf_counter() - start_time

    response_body = [chunk async for chunk in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_body))

    if response_body:
        combined = b''.join(response_body)
        parsed = _safe_json_loads(combined)
        masked = _mask_sensitive_data(parsed)
        logger.debug(f'Response body: {masked}')

    logger.info(
        f'{request.method} {request.url.path} - '
        f'{response.status_code} - {process_time:.4f}s'
    )
    return response
