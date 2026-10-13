from datetime import datetime, timedelta, timezone

from tasks.models import Task
from tasks.services import TaskCleanupService


class TestTaskCleanup:
    async def test_delete_old_done_drops_list_cache(
        self,
        service,
        user,
        create_task_in_db,
        fake_redis,
        db_session,
    ):
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=40)
        fresh = now - timedelta(days=1)
        user_id = user.id

        old_done = await create_task_in_db(
            user_id=user.id,
            title='Old done',
            is_done=True,
            created_at=old,
        )
        fresh_done = await create_task_in_db(
            user_id=user.id,
            title='Fresh done',
            is_done=True,
            created_at=fresh,
        )
        old_open = await create_task_in_db(
            user_id=user.id,
            title='Old open',
            is_done=False,
            created_at=old,
        )
        old_done_id = old_done.id
        fresh_done_id = fresh_done.id
        old_open_id = old_open.id

        cached = await service.get_all_tasks(user_id=user_id)
        assert cached.total == 3
        await fake_redis.set('task:list:other:abc', 'stale')
        await fake_redis.set('rl:ip:1', '1')

        deleted = TaskCleanupService.delete_old_done(30)

        assert deleted == 1
        assert await fake_redis.keys('task:list:*') == []
        assert await fake_redis.get('rl:ip:1') == '1'

        db_session.expire_all()
        again = await service.get_all_tasks(user_id=user_id)
        assert again.total == 2
        assert {item.title for item in again.items} == {
            'Fresh done',
            'Old open',
        }
        assert await db_session.get(Task, old_done_id) is None
        assert await db_session.get(Task, fresh_done_id) is not None
        assert await db_session.get(Task, old_open_id) is not None

    async def test_cleanup_deletes_rows_when_redis_fails(
        self, user, create_task_in_db, db_session, monkeypatch
    ):
        old = datetime.now(timezone.utc) - timedelta(days=40)
        task = await create_task_in_db(
            user_id=user.id,
            title='Old done',
            is_done=True,
            created_at=old,
        )
        task_id = task.id

        def _down():
            raise ConnectionError('redis down')

        monkeypatch.setattr('common.redis_client.get_sync_redis', _down)

        deleted = TaskCleanupService.delete_old_done(30)

        assert deleted == 1
        db_session.expire_all()
        assert await db_session.get(Task, task_id) is None
