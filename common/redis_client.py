import logging

from redis.asyncio import Redis, from_url

from config import settings

logger = logging.getLogger('app')

_redis: Redis | None = None


async def init_redis() -> Redis | None:
    """Создаёт Redis-клиент и проверяет соединение."""
    global _redis
    try:
        client = from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            'Redis unavailable at %s: %s. '
            'Cache and rate-limit will be disabled.',
            settings.REDIS_URL,
            exc,
        )
        _redis = None
        return None

    _redis = client
    logger.info('Redis connected: %s', settings.REDIS_URL)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis | None:
    """Возвращает текущий клиент. None, если Redis недоступен."""
    return _redis
