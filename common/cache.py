import hashlib
import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from common.redis_client import get_redis
from config import settings
from tasks.dto import TaskListDTO, TaskResponseDTO

logger = logging.getLogger('app')


def _cache_key(user_id: UUID, filters: dict[str, Any]) -> str:
    """Строит ключ из user_id + фильтров."""
    canonical = json.dumps(filters, sort_keys=True, default=str)
    digest = hashlib.sha1(canonical.encode()).hexdigest()[:16]
    return f'task:list:{user_id}:{digest}'


def _json_default(obj: Any) -> str:
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Unsupported type for JSON: {type(obj)}')


def _encode(dto: TaskListDTO) -> str:
    """TaskListDTO → JSON-строка (UUID и datetime → str)."""
    return json.dumps(asdict(dto), default=_json_default)


def _decode(raw: str) -> TaskListDTO:
    """JSON-строка → TaskListDTO (str → UUID, datetime)."""
    data = json.loads(raw)
    items = [
        TaskResponseDTO(
            id=UUID(item['id']),
            title=item['title'],
            description=item['description'],
            is_done=item['is_done'],
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at']),
        )
        for item in data['items']
    ]
    return TaskListDTO(
        items=items,
        total=data['total'],
        limit=data['limit'],
        offset=data['offset'],
    )


async def get_cached(
    user_id: UUID,
    filters: dict[str, Any],
) -> TaskListDTO | None:
    """Возвращает кэш списка задач или None."""
    redis = get_redis()
    if redis is None:
        return None

    key = _cache_key(user_id, filters)
    try:
        raw = await redis.get(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning('Cache read failed for %s: %s', key, exc)
        return None

    if raw is None:
        return None

    try:
        return _decode(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning('Cache decode failed for %s: %s', key, exc)
        return None


async def set_cached(
    user_id: UUID, filters: dict[str, Any], dto: TaskListDTO
) -> None:
    """Сохраняет список задач в Redis с TTL из Settings."""
    redis = get_redis()
    if redis is None:
        return

    key = _cache_key(user_id, filters)
    try:
        await redis.set(key, _encode(dto), ex=settings.CACHE_TTL_SECONDS)
    except Exception as exc:  # noqa: BLE001
        logger.warning('Cache write failed for %s: %s', key, exc)


async def invalidate_user_lists(user_id: UUID) -> None:
    """Удаляет все кэшированные списки задач пользователя."""
    redis = get_redis()
    if redis is None:
        return

    pattern = f'task:list:{user_id}:*'
    try:
        async for key in redis.scan_iter(match=pattern):
            await redis.delete(key)
    except Exception as exc:
        logger.warning('Cache invalidation failed for %s: %s', pattern, exc)
