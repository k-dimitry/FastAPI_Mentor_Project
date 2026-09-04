import uuid
from unittest.mock import ANY

import pytest
from fastapi import status
from httpx import AsyncClient

from tasks.models import Task


class TestTasksEndpoints:
    @pytest.fixture
    async def created_task(self, create_task_in_db, test_user):
        return await create_task_in_db(
            user_id=test_user.id,
            title='Original Task',
            description='Original description',
        )

    async def test_get_tasks_authorized(
        self,
        client: AsyncClient,
        user_token,
        create_task_in_db,
        test_user,
    ):
        await create_task_in_db(
            user_id=test_user.id, title='Task 1', description='desc1'
        )
        await create_task_in_db(user_id=test_user.id, title='Task 2')
        await create_task_in_db(
            user_id=test_user.id, title='Task 3', description='desc3'
        )

        response = await client.get(
            '/api/v1/tasks/?limit=2&offset=1',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'result' in data
        assert 'count' in data
        assert 'next' in data
        assert 'previous' in data

        assert data['count'] == 3
        assert len(data['result']) == 2

        assert data['next'] is None
        assert data['previous'] is not None
        assert 'offset=0' in data['previous']

        for task in data['result']:
            assert set(task.keys()) == {
                'id',
                'title',
                'description',
                'is_done',
                'created_at',
                'updated_at',
            }
            assert isinstance(task['id'], str)
            assert isinstance(task['title'], str)
            assert isinstance(task['description'], (str, type(None)))
            assert isinstance(task['is_done'], bool)
            assert isinstance(task['created_at'], str)
            assert isinstance(task['updated_at'], str)

    async def test_get_tasks_unauthorized(self, client: AsyncClient):
        response = await client.get('/api/v1/tasks/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}

    async def test_create_task_success(
        self, client, user_token, db_session, test_user
    ):
        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'title': 'New Task', 'description': 'desc'},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        expected = {
            'id': ANY,
            'title': 'New Task',
            'description': 'desc',
            'is_done': False,
            'created_at': ANY,
            'updated_at': ANY,
        }
        assert data == expected
        assert isinstance(data['id'], str)
        uuid.UUID(data['id'])
        assert isinstance(data['created_at'], str)
        assert isinstance(data['updated_at'], str)

        task_in_db = await db_session.get(Task, uuid.UUID(data['id']))
        assert task_in_db is not None
        assert task_in_db.title == 'New Task'
        assert task_in_db.description == 'desc'
        assert task_in_db.user_id == test_user.id

    async def test_create_task_unauthorized(self, client: AsyncClient):
        response = await client.post(
            '/api/v1/tasks/',
            json={'title': 'No auth'},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}

    async def test_patch_task_owner(
        self, client, user_token, created_task, db_session
    ):
        task_id = created_task.id
        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'title': 'Updated Title'},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        expected = {
            'id': str(task_id),
            'title': 'Updated Title',
            'description': created_task.description,
            'is_done': created_task.is_done,
            'created_at': ANY,
            'updated_at': ANY,
        }
        assert data == expected
        assert isinstance(data['created_at'], str)
        assert isinstance(data['updated_at'], str)

        db_session.expire_all()
        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db.title == 'Updated Title'
        assert task_in_db.description == created_task.description

    async def test_patch_task_foreign(
        self,
        client: AsyncClient,
        admin_token,
        created_task,
    ):
        task_id = created_task.id
        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'title': 'Hacked'},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

    async def test_get_tasks_filter_is_done(
        self,
        client: AsyncClient,
        user_token,
        create_task_in_db,
        test_user,
    ):
        await create_task_in_db(
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
        assert set(task.keys()) == {
            'id',
            'title',
            'description',
            'is_done',
            'created_at',
            'updated_at',
        }
        assert task['title'] == 'Done Task'
        assert task['is_done'] is True
        assert isinstance(task['id'], str)
        assert isinstance(task['description'], (str, type(None)))
        assert isinstance(task['created_at'], str)
        assert isinstance(task['updated_at'], str)
