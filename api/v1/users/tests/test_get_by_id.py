import uuid
from datetime import datetime

from fastapi import status
from httpx import AsyncClient


class TestUserGetByIdSuccess:
    async def test_get_own_profile(
            self, client: AsyncClient, user_token, test_user
    ):
        response = await client.get(
            f'/api/v1/users/{test_user.id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['id'] == str(test_user.id)
        assert data['username'] == 'testuser'
        assert data['email'] == 'testuser@example.com'
        assert data['first_name'] == 'Test'
        assert data['last_name'] == 'User'
        assert data['birthdate'] is None
        assert data['is_admin'] is False
        assert datetime.fromisoformat(
            data['created_at']) == test_user.created_at
        assert datetime.fromisoformat(
            data['updated_at']) == test_user.updated_at

    async def test_admin_gets_other_profile(
            self, client: AsyncClient, admin_token, test_user
    ):
        response = await client.get(
            f'/api/v1/users/{test_user.id}',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data['id'] == str(test_user.id)
        assert data['username'] == 'testuser'
        assert data['email'] == 'testuser@example.com'
        assert data['first_name'] == 'Test'
        assert data['last_name'] == 'User'
        assert data['birthdate'] is None
        assert data['is_admin'] is False


class TestUserGetByIdForbidden:
    async def test_other_user_profile(
            self, client: AsyncClient, user_token, other_user
    ):
        response = await client.get(
            f'/api/v1/users/{other_user.id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'Not enough permissions to view this user'
        }

    async def test_nonexistent_user_as_regular(
            self, client: AsyncClient, user_token
    ):
        """Обычный user с несуществующим id: проверка прав идёт первой → 403."""
        unknown_id = uuid.uuid4()

        response = await client.get(
            f'/api/v1/users/{unknown_id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'Not enough permissions to view this user'
        }


class TestUserGetByIdNotFound:
    async def test_nonexistent_user_as_admin(
            self, client: AsyncClient, admin_token
    ):
        unknown_id = uuid.uuid4()

        response = await client.get(
            f'/api/v1/users/{unknown_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'User not found'}


class TestUserGetByIdUnauthorized:
    async def test_no_token(self, client: AsyncClient, test_user):
        response = await client.get(f'/api/v1/users/{test_user.id}')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {'detail': 'Not authenticated'}
