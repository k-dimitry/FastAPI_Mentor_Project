from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import status
from httpx import AsyncClient

from tasks.models import Task


class TestAdminCleanup:
    async def test_admin_enqueues_cleanup(
        self,
        client: AsyncClient,
        admin_token,
        test_user,
        create_task_in_db,
        fake_redis,
        db_session,
    ):
        now = datetime.now(timezone.utc)
        old_done = await create_task_in_db(
            user_id=test_user.id,
            title='Old done',
            is_done=True,
            created_at=now - timedelta(days=40),
        )
        fresh_done = await create_task_in_db(
            user_id=test_user.id,
            title='Fresh done',
            is_done=True,
            created_at=now - timedelta(days=1),
        )
        old_done_id = old_done.id
        fresh_done_id = fresh_done.id
        await fake_redis.set('task:list:keep', 'stale')

        response = await client.post(
            '/api/v1/admin/cleanup',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert set(data.keys()) == {'task_id'}
        assert UUID(data['task_id'])

        db_session.expire_all()
        assert await db_session.get(Task, old_done_id) is None
        assert await db_session.get(Task, fresh_done_id) is not None
        assert await fake_redis.get('task:list:keep') is None

    async def test_regular_user_forbidden(
        self,
        client: AsyncClient,
        user_token,
        test_user,
        create_task_in_db,
        fake_redis,
        db_session,
    ):
        old_done = await create_task_in_db(
            user_id=test_user.id,
            title='Old done',
            is_done=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=40),
        )
        task_id = old_done.id
        await fake_redis.set('task:list:keep', 'stale')

        response = await client.post(
            '/api/v1/admin/cleanup',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'Only administrators can access this resource'
        }

        db_session.expire_all()
        assert await db_session.get(Task, task_id) is not None
        assert await fake_redis.get('task:list:keep') == 'stale'

    async def test_no_token(self, client: AsyncClient):
        response = await client.post('/api/v1/admin/cleanup')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}

    async def test_days_must_be_positive(
        self, client: AsyncClient, admin_token
    ):
        response = await client.post(
            '/api/v1/admin/cleanup',
            headers={'Authorization': f'Bearer {admin_token}'},
            params={'days': 0},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        detail = response.json()['detail'][0]
        assert detail['loc'] == ['query', 'days']
        assert detail['type'] == 'greater_than_equal'
