import json
import logging
from time import perf_counter

from fastapi import Request, Response
from fastapi.concurrency import iterate_in_threadpool

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
        else:
            return data
    else:
        return data


def _safe_json_loads(body: bytes):
    try:
        return json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body.decode('utf-8', errors='replace')


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
