from datetime import datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient


class TestTaskStatsTotal:
    async def test_user_sees_only_own_tasks(
            self, client, user_token, create_task_in_db, test_user, other_user
    ):
        await create_task_in_db(
            user_id=test_user.id, title='Mine-1', is_done=True
        )
        await create_task_in_db(
            user_id=test_user.id, title='Mine-2', is_done=False
        )
        await create_task_in_db(
            user_id=other_user.id, title='Other-1', is_done=True
        )
        await create_task_in_db(
            user_id=other_user.id, title='Other-2', is_done=True
        )

        response = await client.get(
            '/api/v1/tasks/stats/total',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'done_count': 1,
            'not_done_count': 1,
            'done_percent': '50.00',
        }

    async def test_admin_sees_only_own_tasks(
            self, client, admin_token, create_task_in_db, test_user
    ):
        await create_task_in_db(
            user_id=test_user.id, title='U-1', is_done=True
        )
        await create_task_in_db(
            user_id=test_user.id, title='U-2', is_done=False
        )

        response = await client.get(
            '/api/v1/tasks/stats/total',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'done_count': 0,
            'not_done_count': 0,
            'done_percent': '0.00',
        }

    async def test_done_percent_calculation(
            self, client, user_token, create_task_in_db, test_user
    ):
        await create_task_in_db(
            user_id=test_user.id, title='D-1', is_done=True
        )
        await create_task_in_db(
            user_id=test_user.id, title='D-2', is_done=True
        )
        await create_task_in_db(
            user_id=test_user.id, title='D-3', is_done=True
        )
        await create_task_in_db(
            user_id=test_user.id, title='N-1', is_done=False
        )

        response = await client.get(
            '/api/v1/tasks/stats/total',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'done_count': 3,
            'not_done_count': 1,
            'done_percent': '75.00',
        }

    async def test_empty(self, client, user_token, test_user):
        response = await client.get(
            '/api/v1/tasks/stats/total',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'done_count': 0,
            'not_done_count': 0,
            'done_percent': '0.00',
        }


class TestTaskStatsByDay:
    async def test_user_sees_only_own(
            self, client, user_token, create_task_in_db, test_user, other_user
    ):
        day = datetime(2026, 9, 14, 8, 0, 0, tzinfo=timezone.utc)
        await create_task_in_db(
            user_id=test_user.id, title='Mine', created_at=day
        )
        await create_task_in_db(
            user_id=other_user.id, title='Other', created_at=day
        )

        response = await client.get(
            '/api/v1/tasks/stats/by-day',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {
                    'day': '2026-09-14',
                    'total_count': 1,
                    'done_count': 0,
                    'not_done_count': 1,
                }
            ]
        }

    async def test_grouped_by_day(
            self, client, user_token, create_task_in_db, test_user
    ):
        day1 = datetime(2026, 9, 14, 8, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 9, 15, 8, 0, 0, tzinfo=timezone.utc)
        await create_task_in_db(
            user_id=test_user.id,
            title='D1-1',
            is_done=True,
            created_at=day1,
        )
        await create_task_in_db(
            user_id=test_user.id,
            title='D1-2',
            is_done=False,
            created_at=day1,
        )
        await create_task_in_db(
            user_id=test_user.id,
            title='D2-1',
            is_done=True,
            created_at=day2,
        )

        response = await client.get(
            '/api/v1/tasks/stats/by-day',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {
                    'day': '2026-09-14',
                    'total_count': 2,
                    'done_count': 1,
                    'not_done_count': 1,
                },
                {
                    'day': '2026-09-15',
                    'total_count': 1,
                    'done_count': 1,
                    'not_done_count': 0,
                },
            ]
        }

    async def test_empty(self, client, user_token, test_user):
        response = await client.get(
            '/api/v1/tasks/stats/by-day',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'items': []}


class TestTaskStatsUnauthorized:
    @pytest.mark.parametrize(
        'path',
        [
            '/api/v1/tasks/stats/total',
            '/api/v1/tasks/stats/by-day',
        ],
    )
    async def test_unauthorized(self, client: AsyncClient, path: str):
        response = await client.get(path)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}
