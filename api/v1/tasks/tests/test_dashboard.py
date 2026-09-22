from datetime import datetime, timezone

from fastapi import status
from httpx import AsyncClient


class TestDashboardUser:
    async def test_user_sees_only_own(
        self, client, user_token, create_task_in_db, test_user, other_user
    ):
        day = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
        await create_task_in_db(
            user_id=test_user.id,
            title='Mine-done',
            is_done=True,
            created_at=day,
        )
        await create_task_in_db(
            user_id=test_user.id,
            title='Mine-open',
            is_done=False,
            created_at=day,
        )
        await create_task_in_db(
            user_id=other_user.id,
            title='Other-done',
            is_done=True,
            created_at=day,
        )

        response = await client.get(
            '/api/v1/tasks/dashboard',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'total': {
                'done_count': 1,
                'not_done_count': 1,
                'done_percent': '50.00',
            },
            'by_day': {
                'items': [
                    {
                        'day': '2026-09-14',
                        'total_count': 2,
                        'done_count': 1,
                        'not_done_count': 1,
                    }
                ]
            },
        }

    async def test_user_empty(self, client, user_token, test_user):
        response = await client.get(
            '/api/v1/tasks/dashboard',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'total': {
                'done_count': 0,
                'not_done_count': 0,
                'done_percent': '0.00',
            },
            'by_day': {'items': []},
        }


class TestDashboardAdmin:
    async def test_admin_sees_global(
        self,
        client,
        admin_token,
        create_task_in_db,
        test_user,
        other_user,
        admin_user,
    ):
        day = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
        await create_task_in_db(
            user_id=test_user.id,
            title='U-done',
            is_done=True,
            created_at=day,
        )
        await create_task_in_db(
            user_id=test_user.id,
            title='U-open',
            is_done=False,
            created_at=day,
        )
        await create_task_in_db(
            user_id=other_user.id,
            title='O-done',
            is_done=True,
            created_at=day,
        )

        response = await client.get(
            '/api/v1/tasks/dashboard',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'total': {
                'done_count': 2,
                'not_done_count': 1,
                'done_percent': '66.67',
            },
            'by_day': {
                'items': [
                    {
                        'day': '2026-09-14',
                        'total_count': 3,
                        'done_count': 2,
                        'not_done_count': 1,
                    }
                ]
            },
        }

    async def test_admin_sees_global_even_with_own_tasks(
        self,
        client,
        admin_token,
        create_task_in_db,
        test_user,
        admin_user,
    ):
        day = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
        await create_task_in_db(
            user_id=test_user.id,
            title='U-done',
            is_done=True,
            created_at=day,
        )

        response = await client.get(
            '/api/v1/tasks/dashboard',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == {
            'done_count': 1,
            'not_done_count': 0,
            'done_percent': '100.00',
        }
        assert response.json()['by_day']['items'] == [
            {
                'day': '2026-09-14',
                'total_count': 1,
                'done_count': 1,
                'not_done_count': 0,
            }
        ]

    async def test_admin_empty(self, client, admin_token, admin_user):
        response = await client.get(
            '/api/v1/tasks/dashboard',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'total': {
                'done_count': 0,
                'not_done_count': 0,
                'done_percent': '0.00',
            },
            'by_day': {'items': []},
        }


class TestDashboardUnauthorized:
    async def test_no_token(self, client: AsyncClient):
        response = await client.get('/api/v1/tasks/dashboard')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}
