import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from common.cache import Cache
from common.cache import cache as default_cache
from config import settings
from tasks.dto import TaskListDTO, TaskResponseDTO


class TaskListCache:
    """Кэш списка задач: знает про TaskListDTO и структуру ключа."""

    PREFIX = 'task:list'

    def __init__(
        self,
        cache: Cache | None = None,
        default_ttl: int | None = None,
    ):
        self._cache = cache if cache is not None else default_cache
        self._default_ttl = (
            default_ttl
            if default_ttl is not None
            else settings.CACHE_TTL_SECONDS
        )

    @classmethod
    def _make_key(cls, user_id: UUID, filters: dict[str, Any]) -> str:
        canonical = json.dumps(filters, sort_keys=True, default=str)
        digest = hashlib.sha1(canonical.encode()).hexdigest()[:16]
        return f'{cls.PREFIX}:{user_id}:{digest}'

    @staticmethod
    def _json_default(obj: Any) -> str:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f'Unsupported type for JSON: {type(obj)}')

    @classmethod
    def _encode(cls, dto: TaskListDTO) -> str:
        return json.dumps(asdict(dto), default=cls._json_default)

    @classmethod
    def _decode(cls, raw: str) -> TaskListDTO:
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

    async def get(
        self, user_id: UUID, filters: dict[str, Any]
    ) -> TaskListDTO | None:
        key = self._make_key(user_id, filters)
        raw = await self._cache.get(key)
        if raw is None:
            return None
        try:
            return self._decode(raw)
        except Exception:
            await self._cache.delete(key)
            return None

    async def set(
        self,
        user_id,
        filters,
        dto,
        ttl: int | None = None,
    ) -> None:
        key = self._make_key(user_id, filters)
        await self._cache.set(
            key,
            self._encode(dto),
            ttl if ttl is not None else self._default_ttl,
        )

    async def invalidate_user_lists(self, user_id: UUID) -> None:
        pattern = f'{self.PREFIX}:{user_id}:*'
        await self._cache.delete_pattern(pattern)
