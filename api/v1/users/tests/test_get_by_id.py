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
        assert data['username'] == str(test_user.username)
        assert data['email'] == str(test_user.email)
        assert data['first_name'] == str(test_user.first_name)
        assert data['last_name'] == str(test_user.last_name)
        assert data['birthdate'] == test_user.birthdate
        assert data['is_admin'] == test_user.is_admin
        assert (
            datetime.fromisoformat(data['created_at'])
            == test_user.created_at
        )
        assert (
            datetime.fromisoformat(data['updated_at'])
            == test_user.updated_at
        )

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
        assert data['username'] == str(test_user.username)
        assert data['email'] == str(test_user.email)
        assert data['first_name'] == str(test_user.first_name)
        assert data['last_name'] == str(test_user.last_name)
        assert data['birthdate'] == test_user.birthdate
        assert data['is_admin'] == test_user.is_admin


class TestUserGetByIdForbidden:
    async def test_get_other_user_profile_looks_missing(
        self, client: AsyncClient, user_token, other_user
    ):
        """Чужой существующий профиль для обычного юзера → 404"""
        response = await client.get(
            f'/api/v1/users/{other_user.id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'User not found'}

    async def test_get_nonexistent_user_as_regular(
        self, client: AsyncClient, user_token
    ):
        """Несуществующий id для обычного юзера → 404."""
        unknown_id = uuid.uuid4()

        response = await client.get(
            f'/api/v1/users/{unknown_id}',
            headers={'Authorization': f'Bearer {user_token}'},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'User not found'}


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