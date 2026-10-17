import uuid
from datetime import datetime, timedelta, timezone

import pytest
import time_machine
from fastapi import status
from httpx import AsyncClient

from common.security import create_access_token
from config import settings
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

    async def test_get_tasks_offset_past_end(
        self, client: AsyncClient, user_token, create_task_in_db, test_user
    ):
        for i in range(5):
            await create_task_in_db(user_id=test_user.id, title=f'Task {i}')

        response = await client.get(
            '/api/v1/tasks/?limit=2&offset=10&order_by=title&direction=asc',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['count'] == 5
        assert data['result'] == []
        assert data['next'] is None
        assert data['previous'] == (
            'http://test/api/v1/tasks/'
            '?limit=2&offset=8&order_by=title&direction=asc'
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

    async def test_create_task_empty_title(
        self, client: AsyncClient, user_token
    ):
        response = await client.post(
            '/api/v1/tasks/',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'title': ''},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response.json() == {
            'detail': [
                {
                    'type': 'string_too_short',
                    'loc': ['body', 'title'],
                    'msg': 'String should have at least 1 character',
                    'input': '',
                    'ctx': {'min_length': 1},
                }
            ]
        }

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

    async def test_patch_task_duplicate_title(
        self,
        client: AsyncClient,
        user_token,
        created_task,
        create_task_in_db,
        test_user,
        db_session,
    ):
        other = await create_task_in_db(
            user_id=test_user.id,
            title='Taken',
        )
        other_id = other.id

        response = await client.patch(
            f'/api/v1/tasks/{other_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'title': created_task.title},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                f"Task '{created_task.title}' already exists for this user."
            )
        }

        db_session.expire_all()
        task_in_db = await db_session.get(Task, other_id)
        assert task_in_db.title == 'Taken'

    async def test_patch_task_empty_title(
        self, client: AsyncClient, user_token, created_task, db_session
    ):
        task_id = created_task.id
        original_title = created_task.title

        response = await client.patch(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'title': ''},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response.json() == {
            'detail': [
                {
                    'type': 'string_too_short',
                    'loc': ['body', 'title'],
                    'msg': 'String should have at least 1 character',
                    'input': '',
                    'ctx': {'min_length': 1},
                }
            ]
        }

        db_session.expire_all()
        task_in_db = await db_session.get(Task, task_id)
        assert task_in_db.title == original_title

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


class TestTasksGetById:
    async def test_get_own_task(
        self, client: AsyncClient, user_token, created_task
    ):
        response = await client.get(
            f'/api/v1/tasks/{created_task.id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == str(created_task.id)
        assert data['title'] == created_task.title
        assert data['description'] == created_task.description
        assert data['is_done'] == created_task.is_done
        assert datetime.fromisoformat(data['created_at']) == (
            created_task.created_at
        )
        assert datetime.fromisoformat(data['updated_at']) == (
            created_task.updated_at
        )

    async def test_get_other_users_task(
        self,
        client: AsyncClient,
        user_token,
        other_user,
        create_task_in_db,
    ):
        foreign = await create_task_in_db(
            user_id=other_user.id, title='Foreign'
        )

        response = await client.get(
            f'/api/v1/tasks/{foreign.id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

    async def test_get_missing_task(
        self, client: AsyncClient, user_token
    ):
        response = await client.get(
            f'/api/v1/tasks/{uuid.uuid4()}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

    async def test_get_invalid_uuid(
        self, client: AsyncClient, user_token
    ):
        response = await client.get(
            '/api/v1/tasks/not-a-uuid',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        detail = response.json()['detail'][0]
        assert detail['loc'] == ['path', 'task_id']
        assert detail['type'] == 'uuid_parsing'

    async def test_get_no_token(
        self, client: AsyncClient, created_task
    ):
        response = await client.get(f'/api/v1/tasks/{created_task.id}')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}


class TestTasksDelete:
    async def test_delete_own_task(
        self, client: AsyncClient, user_token, created_task, db_session
    ):
        task_id = created_task.id

        response = await client.delete(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        db_session.expire_all()
        assert await db_session.get(Task, task_id) is None

    async def test_delete_other_users_task(
        self,
        client: AsyncClient,
        user_token,
        other_user,
        create_task_in_db,
        db_session,
    ):
        foreign = await create_task_in_db(
            user_id=other_user.id, title='Keep me'
        )
        task_id = foreign.id

        response = await client.delete(
            f'/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

        db_session.expire_all()
        kept = await db_session.get(Task, task_id)
        assert kept is not None
        assert kept.title == 'Keep me'

    async def test_delete_missing_task(
        self, client: AsyncClient, user_token
    ):
        response = await client.delete(
            f'/api/v1/tasks/{uuid.uuid4()}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

    async def test_delete_invalid_uuid(
        self, client: AsyncClient, user_token
    ):
        response = await client.delete(
            '/api/v1/tasks/not-a-uuid',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        detail = response.json()['detail'][0]
        assert detail['loc'] == ['path', 'task_id']
        assert detail['type'] == 'uuid_parsing'


class TestTasksUnauthorized:
    @pytest.mark.parametrize(
        'method,path,json_body',
        [
            ('GET', '/api/v1/tasks/', None),
            ('GET', f'/api/v1/tasks/{uuid.uuid4()}', None),
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


class TestTasksBadToken:
    async def test_expired_token(self, client: AsyncClient, test_user):
        token = create_access_token({'sub': str(test_user.id)})
        later = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRE_MINUTES + 1
        )

        with time_machine.travel(later, tick=False):
            response = await client.get(
                '/api/v1/tasks/',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid or expired token'}

    async def test_malformed_token(self, client: AsyncClient):
        response = await client.get(
            '/api/v1/tasks/',
            headers={'Authorization': 'Bearer not-a-jwt'},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Invalid or expired token'}
