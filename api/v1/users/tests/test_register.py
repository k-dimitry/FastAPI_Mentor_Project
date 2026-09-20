import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient

from api.v1.users.tests.conftest import CORRECT_PASSWORD
from users.dto import UserCreateDTO, UserResponseDTO
from users.models import User


class TestUserRegisterSuccess:
    async def test_register_success(
        self, client: AsyncClient, mock_user_service
    ):
        fixed_id = uuid.UUID('11111111-1111-1111-1111-111111111111')
        fixed_dt = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)

        expected_dto = UserResponseDTO(
            id=fixed_id,
            username='newuser',
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            birthdate=date(1995, 1, 1),
            created_at=fixed_dt,
            updated_at=fixed_dt,
            is_admin=False,
        )
        mock_user_service.create_user.return_value = expected_dto

        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': CORRECT_PASSWORD,
            'birthdate': '1995-01-01',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data['id'] == str(fixed_id)
        assert data['username'] == 'newuser'
        assert data['email'] == 'newuser@example.com'
        assert data['first_name'] == 'New'
        assert data['last_name'] == 'User'
        assert data['birthdate'] == '1995-01-01'
        assert data['is_admin'] is False

        created_at = datetime.fromisoformat(data['created_at'])
        updated_at = datetime.fromisoformat(data['updated_at'])
        assert created_at == fixed_dt
        assert updated_at == fixed_dt

        expected_create_dto = UserCreateDTO(
            username='newuser',
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            password=CORRECT_PASSWORD,
            birthdate=date(1995, 1, 1),
        )
        mock_user_service.create_user.assert_called_once_with(
            expected_create_dto
        )

    async def test_register_persists_to_db(
        self, client: AsyncClient, db_session
    ):
        payload = {
            'username': 'persisted',
            'email': 'persisted@example.com',
            'first_name': 'Persisted',
            'last_name': 'User',
            'password': CORRECT_PASSWORD,
            'birthdate': '1995-01-01',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        user_id = uuid.UUID(response.json()['id'])

        db_session.expire_all()
        user_in_db = await db_session.get(User, user_id)
        assert user_in_db is not None
        assert user_in_db.username == 'persisted'
        assert user_in_db.email == 'persisted@example.com'
        assert user_in_db.first_name == 'Persisted'
        assert user_in_db.last_name == 'User'
        assert user_in_db.birthdate == date(1995, 1, 1)
        assert user_in_db.is_admin is False

        assert user_in_db.hashed_password != CORRECT_PASSWORD
        assert len(user_in_db.hashed_password) > 20

    async def test_register_without_birthdate(self, client: AsyncClient):
        payload = {
            'username': 'nobirth',
            'email': 'nobirth@example.com',
            'first_name': 'No',
            'last_name': 'Birthdate',
            'password': CORRECT_PASSWORD,
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['birthdate'] is None


class TestUserRegisterDuplicate:
    @pytest.mark.parametrize(
        'username,email,expected_detail',
        [
            (
                'newuser',
                'different@example.com',
                "User 'newuser' or email 'different@example.com' "
                'already exists.',
            ),
            (
                'different',
                'newuser@example.com',
                "User 'different' or email 'newuser@example.com' "
                'already exists.',
            ),
            (
                'newuser',
                'newuser@example.com',
                "User 'newuser' or email 'newuser@example.com' already exists.",
            ),
        ],
    )
    async def test_register_duplicate(
        self,
        client: AsyncClient,
        registered_user,
        username: str,
        email: str,
        expected_detail: str,
    ):
        payload = {
            'username': username,
            'email': email,
            'first_name': 'New',
            'last_name': 'User',
            'password': CORRECT_PASSWORD,
            'birthdate': '1995-01-01',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {'detail': expected_detail}


class TestUserRegisterValidation:
    @pytest.mark.parametrize(
        'password,expected_error',
        [
            (
                'weak',
                {
                    'type': 'too_short',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value should have at least 8 items '
                        'after validation, not 4'
                    ),
                    'input': 'weak',
                    'ctx': {
                        'field_type': 'Value',
                        'min_length': 8,
                        'actual_length': 4,
                    },
                },
            ),
            (
                'short',
                {
                    'type': 'too_short',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value should have at least 8 items '
                        'after validation, not 5'
                    ),
                    'input': 'short',
                    'ctx': {
                        'field_type': 'Value',
                        'min_length': 8,
                        'actual_length': 5,
                    },
                },
            ),
            (
                '12345678',
                {
                    'type': 'value_error',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value error, Пароль должен содержать '
                        'хотя бы одну заглавную букву'
                    ),
                    'input': '12345678',
                    'ctx': {'error': {}},
                },
            ),
            (
                'nouppercase1!',
                {
                    'type': 'value_error',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value error, Пароль должен содержать '
                        'хотя бы одну заглавную букву'
                    ),
                    'input': 'nouppercase1!',
                    'ctx': {'error': {}},
                },
            ),
            (
                'NOLOWERCASE1!',
                {
                    'type': 'value_error',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value error, Пароль должен содержать '
                        'хотя бы одну строчную букву'
                    ),
                    'input': 'NOLOWERCASE1!',
                    'ctx': {'error': {}},
                },
            ),
            (
                'NoNumber!',
                {
                    'type': 'value_error',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value error, Пароль должен содержать '
                        'хотя бы одну цифру'
                    ),
                    'input': 'NoNumber!',
                    'ctx': {'error': {}},
                },
            ),
            (
                'NoSpecialChar111111',
                {
                    'type': 'value_error',
                    'loc': ['body', 'password'],
                    'msg': (
                        'Value error, Пароль должен содержать '
                        'хотя бы один специальный символ (!@#$%^&*)'
                    ),
                    'input': 'NoSpecialChar111111',
                    'ctx': {'error': {}},
                },
            ),
        ],
    )
    async def test_register_invalid_password(
        self,
        client: AsyncClient,
        password: str,
        expected_error: dict,
    ):
        payload = {
            'username': 'user',
            'email': 'user@example.com',
            'first_name': 'User',
            'last_name': 'User',
            'password': password,
            'birthdate': '1995-01-01',
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response.json() == {'detail': [expected_error]}

    @pytest.mark.parametrize(
        'field,value,expected_error',
        [
            (
                'username',
                'ab',
                {
                    'type': 'string_too_short',
                    'loc': ['body', 'username'],
                    'msg': 'String should have at least 3 characters',
                    'input': 'ab',
                    'ctx': {'min_length': 3},
                },
            ),
            (
                'email',
                'not-an-email',
                {
                    'type': 'value_error',
                    'loc': ['body', 'email'],
                    'msg': (
                        'value is not a valid email address: '
                        'An email address must have an @-sign.'
                    ),
                    'input': 'not-an-email',
                    'ctx': {'reason': 'An email address must have an @-sign.'},
                },
            ),
            (
                'first_name',
                '',
                {
                    'type': 'string_too_short',
                    'loc': ['body', 'first_name'],
                    'msg': 'String should have at least 1 character',
                    'input': '',
                    'ctx': {'min_length': 1},
                },
            ),
            (
                'last_name',
                '',
                {
                    'type': 'string_too_short',
                    'loc': ['body', 'last_name'],
                    'msg': 'String should have at least 1 character',
                    'input': '',
                    'ctx': {'min_length': 1},
                },
            ),
        ],
    )
    async def test_register_invalid_fields(
        self, client: AsyncClient, field, value, expected_error
    ):
        payload = {
            'username': 'user',
            'email': 'user@example.com',
            'first_name': 'User',
            'last_name': 'User',
            'password': CORRECT_PASSWORD,
            'birthdate': '1995-01-01',
            field: value,
        }

        response = await client.post('/api/v1/users/register', json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        body = response.json()

        assert body == {'detail': [expected_error]}
