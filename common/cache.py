import logging

from common.redis_client import get_redis

logger = logging.getLogger('app')


class Cache:
    """Общая обёртка над Redis: get/set/delete по строковому ключу."""

    async def get(self, key: str) -> str | None:
        redis = get_redis()
        if redis is None:
            return None
        try:
            return await redis.get(key)
        except Exception as exc:
            logger.warning('Cache read failed for %s: %s', key, exc)
            return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        redis = get_redis()
        if redis is None:
            return
        try:
            await redis.set(key, value, ex=ttl)
        except Exception as exc:
            logger.warning('Cache write failed for %s: %s', key, exc)

    async def delete(self, key: str) -> None:
        redis = get_redis()
        if redis is None:
            return
        try:
            await redis.delete(key)
        except Exception as exc:
            logger.warning('Cache delete failed for %s: %s', key, exc)

    async def delete_pattern(self, pattern: str) -> None:
        redis = get_redis()
        if redis is None:
            return
        try:
            async for key in redis.scan_iter(match=pattern):
                await redis.delete(key)
        except Exception as exc:
            logger.warning('Cache invalidate failed for %s: %s', pattern, exc)


cache = Cache()
