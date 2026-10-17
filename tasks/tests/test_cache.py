import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from common.cache import Cache
from config import settings
from tasks.cache import TaskListCache
from tasks.dto import (
    TaskCreateDTO,
    TaskListDTO,
    TaskResponseDTO,
    TaskUpdateDTO,
)
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




class TestGenericCache:
    async def test_get_miss_on_empty(self, fake_redis):
        c = Cache()
        assert await c.get('nope') is None

    async def test_set_then_get(self, fake_redis):
        c = Cache()
        await c.set('k', 'v', ttl=60)
        assert await c.get('k') == 'v'

    async def test_delete(self, fake_redis):
        c = Cache()
        await c.set('k', 'v', ttl=60)
        await c.delete('k')
        assert await c.get('k') is None

    async def test_delete_pattern(self, fake_redis):
        c = Cache()
        await c.set('a:1', 'v1', ttl=60)
        await c.set('a:2', 'v2', ttl=60)
        await c.set('b:1', 'v3', ttl=60)
        await c.delete_pattern('a:*')
        assert await c.get('a:1') is None
        assert await c.get('a:2') is None
        assert await c.get('b:1') == 'v3'




class TestTaskListCacheKey:
    def test_same_filters_same_key(self):
        user_id = uuid4()
        filters = {'limit': 20, 'offset': 0, 'order_by': 'created_at'}
        k1 = TaskListCache._make_key(user_id, filters)
        k2 = TaskListCache._make_key(user_id, filters)
        assert k1 == k2

    def test_key_format(self):
        user_id = uuid4()
        key = TaskListCache._make_key(user_id, {'limit': 20})
        assert key.startswith(f'task:list:{user_id}:')
        suffix = key.rsplit(':', 1)[-1]
        assert len(suffix) == 16

    def test_different_filters_different_key(self):
        user_id = uuid4()
        k1 = TaskListCache._make_key(user_id, {'limit': 20})
        k2 = TaskListCache._make_key(user_id, {'limit': 50})
        assert k1 != k2

    def test_filters_order_irrelevant(self):
        user_id = uuid4()
        k1 = TaskListCache._make_key(user_id, {'limit': 20, 'offset': 0})
        k2 = TaskListCache._make_key(user_id, {'offset': 0, 'limit': 20})
        assert k1 == k2

    def test_different_users_different_key(self):
        filters = {'limit': 20}
        k1 = TaskListCache._make_key(uuid4(), filters)
        k2 = TaskListCache._make_key(uuid4(), filters)
        assert k1 != k2




class TestTaskListCacheSerialization:
    def test_roundtrip_empty(self):
        dto = TaskListDTO(items=[], total=0, limit=20, offset=0)
        assert TaskListCache._decode(TaskListCache._encode(dto)) == dto

    def test_roundtrip_with_items(self):
        dto = _make_dto(total=3)
        assert TaskListCache._decode(TaskListCache._encode(dto)) == dto

    def test_roundtrip_preserves_types(self):
        dto = _make_dto(total=1)
        item = TaskListCache._decode(TaskListCache._encode(dto)).items[0]
        assert isinstance(item.id, UUID)
        assert isinstance(item.created_at, datetime)
        assert item.created_at.tzinfo is not None




class TestTaskListCacheGetSet:
    async def test_get_miss_on_empty(self, fake_redis):
        tlc = TaskListCache()
        assert await tlc.get(uuid4(), {'limit': 20}) is None

    async def test_set_then_get_hit(self, fake_redis):
        tlc = TaskListCache()
        user_id = uuid4()
        filters = {'limit': 20, 'offset': 0}
        original = _make_dto(total=2)

        await tlc.set(user_id, filters, original)
        restored = await tlc.get(user_id, filters)

        assert restored == original

    async def test_set_sets_default_ttl(self, fake_redis):
        tlc = TaskListCache()
        user_id = uuid4()
        filters = {'limit': 20}
        await tlc.set(user_id, filters, _make_dto())

        key = TaskListCache._make_key(user_id, filters)
        ttl = await fake_redis.ttl(key)
        assert 0 < ttl <= settings.CACHE_TTL_SECONDS

    async def test_set_ttl_override(self, fake_redis):
        tlc = TaskListCache()
        user_id = uuid4()
        filters = {'limit': 20}
        await tlc.set(user_id, filters, _make_dto(), ttl=100)

        key = TaskListCache._make_key(user_id, filters)
        ttl = await fake_redis.ttl(key)
        assert ttl > settings.CACHE_TTL_SECONDS

    async def test_ttl_expires(self, fake_redis):
        tlc = TaskListCache()
        user_id = uuid4()
        filters = {'limit': 20}

        await tlc.set(user_id, filters, _make_dto(), ttl=1)
        assert await tlc.get(user_id, filters) is not None

        await asyncio.sleep(1.1)

        assert await tlc.get(user_id, filters) is None

    async def test_corrupted_data_removed(self, fake_redis):
        tlc = TaskListCache()
        user_id = uuid4()
        filters = {'limit': 20}
        key = TaskListCache._make_key(user_id, filters)

        await fake_redis.set(key, 'not-a-json')

        assert await tlc.get(user_id, filters) is None
        assert await fake_redis.get(key) is None




class TestTaskListCacheInvalidation:
    async def test_invalidate_removes_user_keys(self, fake_redis):
        tlc = TaskListCache()
        user_id = uuid4()
        await tlc.set(user_id, {'limit': 20}, _make_dto())
        await tlc.set(user_id, {'limit': 50}, _make_dto())
        assert len(await fake_redis.keys('task:list:*')) == 2

        await tlc.invalidate_user_lists(user_id)

        assert await fake_redis.keys('task:list:*') == []

    async def test_invalidate_only_matching_user(self, fake_redis):
        tlc = TaskListCache()
        user_a = uuid4()
        user_b = uuid4()
        await tlc.set(user_a, {'limit': 20}, _make_dto())
        await tlc.set(user_b, {'limit': 20}, _make_dto())

        await tlc.invalidate_user_lists(user_a)

        remaining = await fake_redis.keys('task:list:*')
        assert len(remaining) == 1
        assert str(user_b) in remaining[0]

    async def test_invalidate_missing_key_noop(self, fake_redis):
        tlc = TaskListCache()
        await tlc.invalidate_user_lists(uuid4())




class TestCacheGracefulDegrade:
    async def test_get_without_redis(self, monkeypatch):
        monkeypatch.setattr('common.redis_client._redis', None)
        tlc = TaskListCache()
        assert await tlc.get(uuid4(), {'limit': 20}) is None

    async def test_set_without_redis(self, monkeypatch):
        monkeypatch.setattr('common.redis_client._redis', None)
        tlc = TaskListCache()
        await tlc.set(uuid4(), {'limit': 20}, _make_dto())

    async def test_invalidate_without_redis(self, monkeypatch):
        monkeypatch.setattr('common.redis_client._redis', None)
        tlc = TaskListCache()
        await tlc.invalidate_user_lists(uuid4())




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

    async def test_service_caches_empty_result(
        self, fake_redis, service, user
    ):
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

    async def test_create_task_drops_owner_list_cache(
        self, fake_redis, service, user, other_user, create_task_in_db
    ):
        await create_task_in_db(user_id=user.id, title='kept')
        cached = await service.get_all_tasks(user_id=user.id)
        assert cached.total == 1
        other = await service.get_all_tasks(user_id=other_user.id)
        assert other.total == 0
        other_keys = await fake_redis.keys(f'task:list:{other_user.id}:*')
        assert other_keys

        await service.create_task(
            TaskCreateDTO(title='added'), user_id=user.id
        )

        assert await fake_redis.keys(f'task:list:{user.id}:*') == []
        assert (
            await fake_redis.keys(f'task:list:{other_user.id}:*')
            == other_keys
        )

        fresh = await service.get_all_tasks(user_id=user.id)
        titles = {item.title for item in fresh.items}
        assert titles == {'kept', 'added'}
        still_other = await service.get_all_tasks(user_id=other_user.id)
        assert still_other.total == 0

    async def test_update_task_drops_owner_list_cache(
        self, fake_redis, service, user, other_user
    ):
        created = await service.create_task(
            TaskCreateDTO(title='before'), user_id=user.id
        )
        cached = await service.get_all_tasks(user_id=user.id)
        assert cached.items[0].title == 'before'
        await service.get_all_tasks(user_id=other_user.id)
        other_keys = await fake_redis.keys(f'task:list:{other_user.id}:*')
        assert other_keys

        await service.update_task(
            created.id, TaskUpdateDTO(title='after'), user_id=user.id
        )

        assert await fake_redis.keys(f'task:list:{user.id}:*') == []
        assert (
            await fake_redis.keys(f'task:list:{other_user.id}:*')
            == other_keys
        )

        fresh = await service.get_all_tasks(user_id=user.id)
        assert fresh.total == 1
        assert fresh.items[0].title == 'after'
        still_other = await service.get_all_tasks(user_id=other_user.id)
        assert still_other.total == 0

    async def test_delete_task_drops_owner_list_cache(
        self, fake_redis, service, user, other_user, create_task_in_db
    ):
        first = await create_task_in_db(user_id=user.id, title='stay')
        second = await create_task_in_db(user_id=user.id, title='gone')
        cached = await service.get_all_tasks(user_id=user.id)
        assert cached.total == 2
        await service.get_all_tasks(user_id=other_user.id)
        other_keys = await fake_redis.keys(f'task:list:{other_user.id}:*')
        assert other_keys

        deleted = await service.delete_task(second.id, user_id=user.id)
        assert deleted is True

        assert await fake_redis.keys(f'task:list:{user.id}:*') == []
        assert (
            await fake_redis.keys(f'task:list:{other_user.id}:*')
            == other_keys
        )

        fresh = await service.get_all_tasks(user_id=user.id)
        assert fresh.total == 1
        assert fresh.items[0].id == first.id
        assert fresh.items[0].title == 'stay'
        still_other = await service.get_all_tasks(user_id=other_user.id)
        assert still_other.total == 0