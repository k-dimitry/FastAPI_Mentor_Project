import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from common.cache import (
    _cache_key,
    _decode,
    _encode,
    get_cached,
    invalidate_user_lists,
    set_cached,
)
from config import settings
from tasks.dto import TaskListDTO, TaskResponseDTO
from tasks.models import Task


def _make_dto(total: int = 1) -> TaskListDTO:
    """Фабрика TaskListDTO с детерминированными значениями."""
    dt = datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)
    items = [
        TaskResponseDTO(
            id=UUID(f'{i:08d}-0000-0000-0000-000000000000'),
            title=f'task-{i}',
            description=None if i % 2 == 0 else f'desc-{i}',
            is_done=bool(i % 2),
            created_at=dt,
            updated_at=dt,
        )
        for i in range(total)
    ]
    return TaskListDTO(items=items, total=total, limit=20, offset=0)


class TestCacheKey:
    def test_same_filters_same_key(self):
        user_id = uuid4()
        filters = {'limit': 20, 'offset': 0, 'order_by': 'created_at'}
        assert _cache_key(user_id, filters) == _cache_key(user_id, filters)

    def test_key_format(self):
        user_id = uuid4()
        key = _cache_key(user_id, {'limit': 20})
        assert key.startswith(f'task:list:{user_id}:')
        suffix = key.rsplit(':', 1)[-1]
        assert len(suffix) == 16  # sha1[:16]

    def test_different_filters_different_key(self):
        user_id = uuid4()
        k1 = _cache_key(user_id, {'limit': 20})
        k2 = _cache_key(user_id, {'limit': 50})
        assert k1 != k2

    def test_filters_order_irrelevant(self):
        user_id = uuid4()
        k1 = _cache_key(user_id, {'limit': 20, 'offset': 0})
        k2 = _cache_key(user_id, {'offset': 0, 'limit': 20})
        assert k1 == k2

    def test_different_users_different_key(self):
        filters = {'limit': 20}
        assert _cache_key(uuid4(), filters) != _cache_key(uuid4(), filters)


class TestCacheSerialization:
    def test_roundtrip_empty(self):
        dto = TaskListDTO(items=[], total=0, limit=20, offset=0)
        assert _decode(_encode(dto)) == dto

    def test_roundtrip_with_items(self):
        dto = _make_dto(total=3)
        assert _decode(_encode(dto)) == dto

    def test_roundtrip_preserves_types(self):
        dto = _make_dto(total=1)
        item = _decode(_encode(dto)).items[0]
        assert isinstance(item.id, UUID)
        assert isinstance(item.created_at, datetime)
        assert item.created_at.tzinfo is not None


class TestCacheGetSet:
    async def test_get_miss_on_empty(self, fake_redis):
        assert await get_cached(uuid4(), {'limit': 20}) is None

    async def test_set_then_get_hit(self, fake_redis):
        user_id = uuid4()
        filters = {'limit': 20, 'offset': 0}
        original = _make_dto(total=2)

        await set_cached(user_id, filters, original)
        restored = await get_cached(user_id, filters)

        assert restored == original

    async def test_set_sets_ttl(self, fake_redis):
        user_id = uuid4()
        filters = {'limit': 20}
        await set_cached(user_id, filters, _make_dto())

        key = _cache_key(user_id, filters)
        ttl = await fake_redis.ttl(key)
        assert 0 < ttl <= settings.CACHE_TTL_SECONDS

    async def test_ttl_expires(self, fake_redis, monkeypatch):
        monkeypatch.setattr(settings, 'CACHE_TTL_SECONDS', 1)
        user_id = uuid4()
        filters = {'limit': 20}

        await set_cached(user_id, filters, _make_dto())
        assert await get_cached(user_id, filters) is not None

        await asyncio.sleep(1.1)

        assert await get_cached(user_id, filters) is None


class TestCacheInvalidation:
    async def test_invalidate_removes_user_keys(self, fake_redis):
        user_id = uuid4()
        await set_cached(user_id, {'limit': 20}, _make_dto())
        await set_cached(user_id, {'limit': 50}, _make_dto())
        assert len(await fake_redis.keys('task:list:*')) == 2

        await invalidate_user_lists(user_id)

        assert await fake_redis.keys('task:list:*') == []

    async def test_invalidate_only_matching_user(self, fake_redis):
        user_a = uuid4()
        user_b = uuid4()
        await set_cached(user_a, {'limit': 20}, _make_dto())
        await set_cached(user_b, {'limit': 20}, _make_dto())

        await invalidate_user_lists(user_a)

        remaining = await fake_redis.keys('task:list:*')
        assert len(remaining) == 1
        assert str(user_b) in remaining[0]

    async def test_invalidate_missing_key_noop(self, fake_redis):
        await invalidate_user_lists(uuid4())


class TestCacheGracefulDegrade:
    async def test_get_cached_without_redis(self, monkeypatch):
        monkeypatch.setattr('common.redis_client._redis', None)
        assert await get_cached(uuid4(), {'limit': 20}) is None

    async def test_set_cached_without_redis(self, monkeypatch):
        monkeypatch.setattr('common.redis_client._redis', None)
        await set_cached(uuid4(), {'limit': 20}, _make_dto())

    async def test_invalidate_without_redis(self, monkeypatch):
        monkeypatch.setattr('common.redis_client._redis', None)
        await invalidate_user_lists(uuid4())


class TestTaskServiceCache:
    async def test_service_populates_cache_on_miss(
        self, fake_redis, service, user, create_task_in_db
    ):
        await create_task_in_db(user_id=user.id, title='t-1')

        result = await service.get_all_tasks(user_id=user.id)

        assert result.total == 1
        assert result.items[0].title == 't-1'
        keys = await fake_redis.keys('task:list:*')
        assert len(keys) == 1

    async def test_service_caches_empty_result(self, fake_redis, service, user):
        result = await service.get_all_tasks(user_id=user.id)

        assert result.total == 0
        keys = await fake_redis.keys('task:list:*')
        assert len(keys) == 1

    async def test_service_returns_cached_on_hit(
        self, fake_redis, service, user, create_task_in_db
    ):
        task = await create_task_in_db(user_id=user.id, title='t-1')

        result1 = await service.get_all_tasks(user_id=user.id)
        assert result1.total == 1

        task_obj = await service.db.get(Task, task.id)
        await service.db.delete(task_obj)
        await service.db.commit()

        result2 = await service.get_all_tasks(user_id=user.id)
        assert result2.total == 1
        assert result2.items[0].title == 't-1'
