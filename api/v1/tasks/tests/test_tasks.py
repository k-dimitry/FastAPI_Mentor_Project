import uuid

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

        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'result' in data
        assert 'count' in data
        assert 'next' in data
        assert 'previous' in data

        assert data['count'] == 2
        assert len(data['result']) == 2

        for task in data['result']:
            assert set(task.keys()) == {
                'id',
                'title',
                'description',
                'is_done',
                'created_at',
                'updated_at',
            }
            # id должен быть строкой (UUID)
            assert isinstance(task['id'], str)
            assert isinstance(task['title'], str)
            assert isinstance(task['is_done'], bool)

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

        assert data['title'] == 'New Task'
        assert data['description'] == 'desc'
        assert data['is_done'] is False
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

        task_in_db = await db_session.get(Task, uuid.UUID(data['id']))
        assert task_in_db is not None
        assert task_in_db.title == 'New Task'
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

        assert data['title'] == 'Updated Title'
        assert data['description'] == created_task.description
        assert data['is_done'] == created_task.is_done

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
        assert task['title'] == 'Done Task'
        assert task['is_done'] is True
        assert 'id' in task
