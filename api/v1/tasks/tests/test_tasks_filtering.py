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

    async def test_created_from_and_created_to(
        self, client: AsyncClient, user_token, twelve_tasks
    ):
        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            params={
                'created_from': '2026-09-14T08:05:00+00:00',
                'created_to': '2026-09-14T08:07:00+00:00',
                'order_by': 'title',
                'direction': 'asc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 3
        assert [task['title'] for task in data['result']] == [
            'Task 5',
            'Task 6',
            'Task 7',
        ]
        assert [task['id'] for task in data['result']] == [
            str(twelve_tasks[5].id),
            str(twelve_tasks[6].id),
            str(twelve_tasks[7].id),
        ]


class TestTasksSearch:
    async def test_search_percent_is_literal(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        await create_task_in_db(user_id=test_user.id, title='100% done')
        await create_task_in_db(user_id=test_user.id, title='Other')

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            params={'query': '%'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['result'][0]['title'] == '100% done'

    async def test_search_underscore_is_literal(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        await create_task_in_db(user_id=test_user.id, title='a_b')
        await create_task_in_db(user_id=test_user.id, title='axb')

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            params={'query': 'a_b'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['result'][0]['title'] == 'a_b'

    async def test_search_description(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        await create_task_in_db(
            user_id=test_user.id,
            title='Plain',
            description='hidden needle',
        )
        await create_task_in_db(
            user_id=test_user.id, title='Other', description='nope'
        )

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            params={'query': 'needle'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 1
        assert data['result'][0]['title'] == 'Plain'


class TestTasksOrderByUpdatedAt:
    async def test_order_by_updated_at_desc(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        await create_task_in_db(
            user_id=test_user.id,
            title='Older edit',
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        await create_task_in_db(
            user_id=test_user.id,
            title='Newer edit',
            updated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            params={'order_by': 'updated_at', 'direction': 'desc'},
        )

        assert response.status_code == status.HTTP_200_OK
        titles = [task['title'] for task in response.json()['result']]
        assert titles == ['Newer edit', 'Older edit']


class TestTasksSortValidation:
    @pytest.mark.parametrize(
        'params,field',
        [
            ({'order_by': 'user_id'}, 'order_by'),
            ({'direction': 'sideways'}, 'direction'),
        ],
    )
    async def test_unknown_sort_is_rejected(
        self, client: AsyncClient, user_token, params, field
    ):
        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            params=params,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        detail = response.json()['detail'][0]
        assert detail['loc'] == ['query', field]
        assert detail['type'] == 'literal_error'
