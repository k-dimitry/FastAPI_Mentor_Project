from datetime import datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient


class TestTasksFilteringAndOrdering:
    @pytest.fixture
    async def twelve_tasks(self, create_task_in_db, test_user):
        base = datetime(2026, 9, 14, 8, 0, 0, tzinfo=timezone.utc)
        tasks = {}
        for i in range(1, 13):
            task = await create_task_in_db(
                user_id=test_user.id,
                title=f'Task {i}',
                description=f'Task {i} description',
                is_done=i in (6, 7, 8, 9, 10, 11),
                created_at=base.replace(minute=i),
            )
            tasks[i] = task
        return tasks

    async def test_list_order_by_created_at_desc(
        self, client: AsyncClient, user_token, twelve_tasks
    ):
        expected_titles = ['Task 12', 'Task 11', 'Task 10', 'Task 9', 'Task 8']
        expected_is_done = [False, True, True, True, True]

        response = await client.get(
            '/api/v1/tasks/'
            '?limit=5&offset=0&order_by=created_at&direction=desc',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['count'] == 12
        assert len(data['result']) == 5

        assert data['next'] == (
            'http://test/api/v1/tasks/'
            '?limit=5&offset=5&order_by=created_at&direction=desc'
        )
        assert data['previous'] is None

        for index, task in enumerate(data['result']):
            expected_num = 12 - index
            assert task['id'] == str(twelve_tasks[expected_num].id)
            assert task['title'] == expected_titles[index]
            assert task['description'] == f'Task {expected_num} description'
            assert task['is_done'] is expected_is_done[index]

            created_at = datetime.fromisoformat(
                task['created_at'].replace('Z', '+00:00')
            )
            assert created_at.replace(tzinfo=None) == datetime(
                2026, 9, 14, 8, expected_num, 0
            )

    async def test_list_filter_is_done_order_by_title_asc(
        self, client: AsyncClient, user_token, twelve_tasks
    ):

        expected_titles = ['Task 6', 'Task 7', 'Task 8', 'Task 9']
        expected_ids = [
            str(twelve_tasks[6].id),
            str(twelve_tasks[7].id),
            str(twelve_tasks[8].id),
            str(twelve_tasks[9].id),
        ]

        response = await client.get(
            '/api/v1/tasks/'
            '?limit=4&offset=2&is_done=true&order_by=title&direction=asc',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['count'] == 6
        assert len(data['result']) == 4

        assert data['next'] is None
        assert data['previous'] == (
            'http://test/api/v1/tasks/'
            '?limit=4&offset=0&is_done=true&order_by=title&direction=asc'
        )

        for index, task in enumerate(data['result']):
            assert task['id'] == expected_ids[index]
            assert task['title'] == expected_titles[index]
            assert (
                task['description']
                == f'Task {expected_titles[index].split()[-1]} description'
            )
            assert task['is_done'] is True
