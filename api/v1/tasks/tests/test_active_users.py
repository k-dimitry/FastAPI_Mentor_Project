from fastapi import status
from httpx import AsyncClient


class TestTaskActiveUsersSuccess:
    async def test_admin_sees_sorted_top(
        self,
        client: AsyncClient,
        admin_token,
        create_user_in_db,
        create_task_in_db,
    ):
        user_a = await create_user_in_db(
            username='user_a', email='a@example.com'
        )
        user_b = await create_user_in_db(
            username='user_b', email='b@example.com'
        )
        user_c = await create_user_in_db(
            username='user_c', email='c@example.com'
        )

        for i in range(3):
            await create_task_in_db(
                user_id=user_a.id, title=f'a-{i}', is_done=False
            )
        await create_task_in_db(
            user_id=user_b.id, title='b-open', is_done=False
        )
        await create_task_in_db(
            user_id=user_b.id, title='b-done', is_done=True
        )
        for i in range(2):
            await create_task_in_db(
                user_id=user_c.id, title=f'c-{i}', is_done=False
            )

        response = await client.get(
            '/api/v1/tasks/active-users',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {
                    'user_id': str(user_a.id),
                    'username': 'user_a',
                    'email': 'a@example.com',
                    'open_tasks': 3,
                },
                {
                    'user_id': str(user_c.id),
                    'username': 'user_c',
                    'email': 'c@example.com',
                    'open_tasks': 2,
                },
                {
                    'user_id': str(user_b.id),
                    'username': 'user_b',
                    'email': 'b@example.com',
                    'open_tasks': 1,
                },
            ]
        }

    async def test_admin_sees_only_users_with_open_tasks(
        self,
        client: AsyncClient,
        admin_token,
        create_user_in_db,
        create_task_in_db,
    ):
        user_a = await create_user_in_db(
            username='only_done', email='d@example.com'
        )
        user_b = await create_user_in_db(
            username='with_open', email='o@example.com'
        )
        await create_task_in_db(
            user_id=user_a.id, title='done', is_done=True
        )
        await create_task_in_db(
            user_id=user_b.id, title='open', is_done=False
        )

        response = await client.get(
            '/api/v1/tasks/active-users',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {
                    'user_id': str(user_b.id),
                    'username': 'with_open',
                    'email': 'o@example.com',
                    'open_tasks': 1,
                }
            ]
        }

    async def test_admin_empty(
        self, client: AsyncClient, admin_token
    ):
        response = await client.get(
            '/api/v1/tasks/active-users',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'items': []}


class TestTaskActiveUsersForbidden:
    async def test_regular_user(
        self, client: AsyncClient, user_token
    ):
        response = await client.get(
            '/api/v1/tasks/active-users',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'Only administrators can access this resource'
        }


class TestTaskActiveUsersUnauthorized:
    async def test_no_token(self, client: AsyncClient):
        response = await client.get('/api/v1/tasks/active-users')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}