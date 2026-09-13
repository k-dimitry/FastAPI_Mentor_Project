import uuid
from datetime import datetime, timezone

import time_machine
from fastapi import status
from httpx import AsyncClient

from conftest import as_naive_utc
from tasks.models import Task


class TestTasksList:
    async def test_get_tasks_authorized(
        self, client: AsyncClient, user_token, tasks_for_user
    ):

        response = await client.get(
            '/api/v1/tasks/?limit=2&offset=1&order_by=title&direction=asc',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['count'] == 3
        assert len(data['result']) == 2
        assert data['next'] is None
        assert data['previous'] == (
            'http://test/api/v1/tasks/'
            '?limit=2&offset=0&order_by=title&direction=asc'
        )

        first, second = data['result']

        assert first['id'] == str(tasks_for_user['task_2'].id)
        assert first['title'] == 'Task 2'
        assert first['description'] is None
        assert first['is_done'] is False

        assert second['id'] == str(tasks_for_user['task_3'].id)
        assert second['title'] == 'Task 3'
        assert second['description'] == 'desc3'
        assert second['is_done'] is False

    async def test_get_tasks_pagination_has_next(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        for i in range(5):
            await create_task_in_db(user_id=test_user.id, title=f'Task {i}')

        response = await client.get(
            '/api/v1/tasks/?limit=2&offset=0&order_by=title&direction=asc',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        data = response.json()
        assert data['count'] == 5
        assert len(data['result']) == 2
        assert data['next'] == (
            'http://test/api/v1/tasks/'
            '?limit=2&offset=2&order_by=title&direction=asc'
        )
        assert data['previous'] is None

    async def test_get_tasks_pagination_middle_page(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        for i in range(5):
            await create_task_in_db(user_id=test_user.id, title=f'Task {i}')

        response = await client.get(
            '/api/v1/tasks/?limit=2&offset=2&order_by=title&direction=asc',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        data = response.json()
        assert data['count'] == 5
        assert len(data['result']) == 2
        assert data['next'] == (
            'http://test/api/v1/tasks/'
            '?limit=2&offset=4&order_by=title&direction=asc'
        )
        assert data['previous'] == (
            'http://test/api/v1/tasks/'
            '?limit=2&offset=0&order_by=title&direction=asc'
        )

    async def test_get_tasks_unauthorized(self, client: AsyncClient):
        response = await client.get('/api/v1/tasks/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}

    async def test_get_tasks_filter_is_done(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        done = await create_task_in_db(
            user_id=test_user.id, title='Done Task', is_done=True
        )
        await create_task_in_db(
            user_id=test_user.id, title='Open Task', is_done=False
        )

        response = await client.get(
            '/api/v1/tasks/?is_done=true',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['count'] == 1
        assert len(data['result']) == 1

        task = data['result'][0]
        assert task['id'] == str(done.id)
        assert task['title'] == 'Done Task'
        assert task['description'] is None
        assert task['is_done'] is True


class TestTasksCreate:
    @time_machine.travel(
        datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc),
        tick=False,
    )
    async def test_create_task_success(
        self, client, user_token, db_session, test_user
    ):
        payload = {'title': 'New Task', 'description': 'desc'}
        expected_dt = datetime(2026, 8, 30, 12, 30, 0, tzinfo=timezone.utc)

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        task_id = uuid.UUID(data['id'])

        assert data['title'] == 'New Task'
        assert data['description'] == 'desc'
        assert data['is_done'] is False

        created_at = datetime.fromisoformat(
            data['created_at'].replace('Z', '+00:00')
        )
        updated_at = datetime.fromisoformat(
            data['updated_at'].replace('Z', '+00:00')
        )

        expected_naive = datetime(2026, 8, 30, 12, 30)
        assert as_naive_utc(created_at) == expected_naive
        assert as_naive_utc(updated_at) == expected_naive

        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db is not None
        assert task_in_db.title == 'New Task'
        assert task_in_db.description == 'desc'
        assert task_in_db.is_done is False
        assert task_in_db.user_id == test_user.id

    async def test_create_task_without_description(
        self, client: AsyncClient, user_token, db_session
    ):
        payload = {'title': 'No description'}

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['title'] == 'No description'
        assert data['description'] is None
        assert data['is_done'] is False

        task_in_db = await db_session.get(Task, uuid.UUID(data['id']))
        assert task_in_db.description is None

    async def test_create_task_duplicate_title(
        self, client: AsyncClient, user_token, created_task
    ):
        payload = {'title': created_task.title}

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_create_task_unauthorized(self, client: AsyncClient):
        response = await client.post(
            '/api/v1/tasks/',
            json={'title': 'No auth'},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}


class TestTasksPatch:
    async def test_patch_task_title(
        self, client: AsyncClient, user_token, created_task, db_session
    ):
        task_id = created_task.id
        payload = {'title': 'Updated Title'}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['id'] == str(task_id)
        assert data['title'] == 'Updated Title'
        assert data['description'] == created_task.description
        assert data['is_done'] == created_task.is_done

        db_session.expire_all()
        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db.title == 'Updated Title'
        assert task_in_db.description == created_task.description
        assert task_in_db.is_done == created_task.is_done

    async def test_patch_task_description_to_none(
        self, client: AsyncClient, user_token, created_task, db_session
    ):
        task_id = created_task.id
        payload = {'description': None}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['title'] == created_task.title
        assert data['description'] is None

        db_session.expire_all()
        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db.description is None

    async def test_patch_task_is_done(
        self, client: AsyncClient, user_token, created_task
    ):
        task_id = created_task.id
        payload = {'is_done': True}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_done'] is True
        assert data['title'] == created_task.title
        assert data['description'] == created_task.description

    async def test_patch_task_foreign(
        self, client: AsyncClient, admin_token, created_task, db_session
    ):
        task_id = created_task.id
        original_title = created_task.title
        payload = {'title': 'Hacked'}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

        db_session.expire_all()
        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db.title == original_title

    async def test_patch_task_nonexistent(
        self, client: AsyncClient, user_token
    ):
        task_id = uuid.uuid4()
        payload = {'title': 'Whatever'}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}
