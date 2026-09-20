import uuid
from datetime import datetime, timezone

import pytest
import time_machine
from fastapi import status
from httpx import AsyncClient

from tasks.dto import TaskCreateDTO, TaskResponseDTO, TaskUpdateDTO
from tasks.exceptions import TaskAlreadyExistsError
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
    async def test_create_task_success(
        self, client, user_token, mock_task_service, test_user
    ):
        fixed_id = uuid.UUID('11111111-1111-1111-1111-111111111111')
        fixed_dt = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)

        mock_task_service.create_task.return_value = TaskResponseDTO(
            id=fixed_id,
            title='New Task',
            description='desc',
            is_done=False,
            created_at=fixed_dt,
            updated_at=fixed_dt,
        )
        payload = {'title': 'New Task', 'description': 'desc'}

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data['id'] == str(fixed_id)
        assert data['title'] == 'New Task'
        assert data['description'] == 'desc'
        assert data['is_done'] is False
        assert datetime.fromisoformat(data['created_at']) == fixed_dt
        assert datetime.fromisoformat(data['updated_at']) == fixed_dt

        expected_dto = TaskCreateDTO(
            title='New Task',
            description='desc',
            is_done=False,
        )
        mock_task_service.create_task.assert_called_once_with(
            expected_dto, user_id=test_user.id
        )

    @time_machine.travel(
        datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc),
        tick=False,
    )
    async def test_create_task_success_persists_to_db(
        self, client, user_token, db_session, test_user
    ):
        payload = {'title': 'Persisted Task', 'description': 'desc'}
        expected = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        task_id = uuid.UUID(data['id'])

        assert data['title'] == 'Persisted Task'
        assert data['description'] == 'desc'
        assert data['is_done'] is False
        assert datetime.fromisoformat(data['created_at']) == expected
        assert datetime.fromisoformat(data['updated_at']) == expected

        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db is not None
        assert task_in_db.title == 'Persisted Task'
        assert task_in_db.description == 'desc'
        assert task_in_db.is_done is False
        assert task_in_db.user_id == test_user.id
        assert task_in_db.created_at == expected
        assert task_in_db.updated_at == expected

    async def test_create_task_without_description(
        self, client, user_token, mock_task_service, test_user
    ):
        fixed_id = uuid.UUID('22222222-2222-2222-2222-222222222222')
        fixed_dt = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)

        mock_task_service.create_task.return_value = TaskResponseDTO(
            id=fixed_id,
            title='No description',
            description=None,
            is_done=False,
            created_at=fixed_dt,
            updated_at=fixed_dt,
        )

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'title': 'No description'},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['title'] == 'No description'
        assert data['description'] is None
        assert data['is_done'] is False

        expected_dto = TaskCreateDTO(
            title='No description',
            description=None,
            is_done=False,
        )
        mock_task_service.create_task.assert_called_once_with(
            expected_dto, user_id=test_user.id
        )

    async def test_create_task_duplicate_title(
        self, client, user_token, mock_task_service, test_user
    ):
        mock_task_service.create_task.side_effect = TaskAlreadyExistsError(
            "Task 'Duplicate' already exists for this user."
        )
        payload = {'title': 'Duplicate'}

        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': "Task 'Duplicate' already exists for this user."
        }

        expected_dto = TaskCreateDTO(
            title='Duplicate',
            description=None,
            is_done=False,
        )
        mock_task_service.create_task.assert_called_once_with(
            expected_dto, user_id=test_user.id
        )


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
        self, client, user_token, mock_task_service, test_user, created_task
    ):
        task_id = created_task.id
        fixed_dt = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)
        mock_task_service.update_task.return_value = TaskResponseDTO(
            id=task_id,
            title=created_task.title,
            description=None,
            is_done=created_task.is_done,
            created_at=created_task.created_at,
            updated_at=fixed_dt,
        )
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
        assert data['is_done'] == created_task.is_done

        expected_dto = TaskUpdateDTO(description=None)
        mock_task_service.update_task.assert_called_once_with(
            task_id, expected_dto, user_id=test_user.id
        )

    async def test_patch_task_is_done(
        self, client, user_token, mock_task_service, test_user, created_task
    ):
        task_id = created_task.id
        fixed_dt = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)
        mock_task_service.update_task.return_value = TaskResponseDTO(
            id=task_id,
            title=created_task.title,
            description=created_task.description,
            is_done=True,
            created_at=created_task.created_at,
            updated_at=fixed_dt,
        )
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

        expected_dto = TaskUpdateDTO(is_done=True)
        mock_task_service.update_task.assert_called_once_with(
            task_id, expected_dto, user_id=test_user.id
        )

    async def test_patch_task_unset_fields_are_unset(
        self, client, user_token, mock_task_service, test_user, created_task
    ):
        """Поля, не переданные в запросе, должны остаться UNSET в DTO."""
        task_id = created_task.id
        fixed_dt = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)
        mock_task_service.update_task.return_value = TaskResponseDTO(
            id=task_id,
            title='Only title',
            description=created_task.description,
            is_done=created_task.is_done,
            created_at=created_task.created_at,
            updated_at=fixed_dt,
        )
        payload = {'title': 'Only title'}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        expected_dto = TaskUpdateDTO(title='Only title')
        assert expected_dto.description_is_set is False
        assert expected_dto.is_done_is_set is False

        mock_task_service.update_task.assert_called_once_with(
            task_id, expected_dto, user_id=test_user.id
        )

    async def test_patch_task_other_user(
        self,
        client,
        admin_token,
        mock_task_service,
        admin_user,
        created_task,
    ):
        task_id = created_task.id
        mock_task_service.update_task.return_value = None
        payload = {'title': 'Hacked'}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

        expected_dto = TaskUpdateDTO(title='Hacked')
        mock_task_service.update_task.assert_called_once_with(
            task_id, expected_dto, user_id=admin_user.id
        )

    async def test_patch_task_no_exist(
        self, client, user_token, mock_task_service, test_user
    ):
        task_id = uuid.uuid4()
        mock_task_service.update_task.return_value = None
        payload = {'title': 'Whatever'}

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

        expected_dto = TaskUpdateDTO(title='Whatever')
        mock_task_service.update_task.assert_called_once_with(
            task_id, expected_dto, user_id=test_user.id
        )


class TestTasksUnauthorized:
    @pytest.mark.parametrize(
        'method,path,json_body',
        [
            ('GET', '/api/v1/tasks/', None),
            ('POST', '/api/v1/tasks/', {'title': 'No auth'}),
            ('PATCH', f'/api/v1/tasks/{uuid.uuid4()}', {'title': 'No auth'}),
            ('DELETE', f'/api/v1/tasks/{uuid.uuid4()}', None),
        ],
    )
    async def test_unauthorized(
        self,
        client: AsyncClient,
        method: str,
        path: str,
        json_body: dict | None,
    ):
        response = await client.request(method, path, json=json_body)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}
