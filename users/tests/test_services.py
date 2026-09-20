from datetime import date, datetime, timezone

import pytest
import time_machine

from users.dto import UserCreateDTO
from users.exceptions import UserAlreadyExistsError
from users.models import User

pytestmark = pytest.mark.asyncio


class TestUserService:
    async def test_create_user(self, service):
        dto = UserCreateDTO(
            username='newuser',
            email='new@example.com',
            first_name='New',
            last_name='User',
            password='Str0ngPass!',
            birthdate=date(1985, 3, 20),
        )

        result = await service.create_user(dto)

        assert result.username == 'newuser'
        assert result.email == 'new@example.com'
        assert result.first_name == 'New'
        assert result.last_name == 'User'
        assert result.birthdate == date(1985, 3, 20)
        assert result.is_admin is False

        user_in_db = await service.db.get(User, result.id)
        assert user_in_db is not None
        assert user_in_db.birthdate == date(1985, 3, 20)
        assert user_in_db.hashed_password != 'Str0ngPass!'
        assert len(user_in_db.hashed_password) > 20

    async def test_create_user_without_birthdate(self, service):
        dto = UserCreateDTO(
            username='nobd',
            email='nobd@example.com',
            first_name='No',
            last_name='Birthdate',
            password='Str0ngPass!',
            birthdate=None,
        )

        result = await service.create_user(dto)

        assert result.birthdate is None
        user_in_db = await service.db.get(User, result.id)
        assert user_in_db.birthdate is None

    @time_machine.travel(
        datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc),
        tick=False,
    )
    async def test_create_user_timestamps(self, service):
        dto = UserCreateDTO(
            username='timeuser',
            email='time@example.com',
            first_name='Time',
            last_name='User',
            password='Str0ngPass!',
        )
        expected = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)

        result = await service.create_user(dto)

        assert result.created_at == expected
        assert result.updated_at == expected

    @pytest.mark.parametrize(
        'username,email',
        [
            ('existing', 'different@example.com'),
            ('different', 'existing@example.com'),
            ('existing', 'existing@example.com'),
        ],
    )
    async def test_create_duplicate_user(
        self, service, existing_user, username, email
    ):
        dto = UserCreateDTO(
            username=username,
            email=email,
            first_name='Dup',
            last_name='User',
            password='Str0ngPass!',
        )

        with pytest.raises(UserAlreadyExistsError):
            await service.create_user(dto)

    async def test_authenticate_user_success(self, service, existing_user):
        username = 'existing'
        password = 'Str0ngPass!'

        authenticated = await service.authenticate_user(username, password)

        assert authenticated is not None
        assert authenticated.id == existing_user.id
        assert authenticated.username == existing_user.username
        assert authenticated.email == existing_user.email
        assert authenticated.first_name == existing_user.first_name
        assert authenticated.last_name == existing_user.last_name
        assert authenticated.birthdate == existing_user.birthdate
        assert authenticated.is_admin == existing_user.is_admin

    async def test_authenticate_user_by_email(self, service, existing_user):
        email = 'existing@example.com'
        password = 'Str0ngPass!'

        authenticated = await service.authenticate_user(email, password)

        assert authenticated is not None
        assert authenticated.id == existing_user.id

    async def test_authenticate_user_wrong_password(
        self, service, existing_user
    ):
        username = 'existing'
        wrong_password = 'WrongPass'

        authenticated = await service.authenticate_user(
            username, wrong_password
        )

        assert authenticated is None

    async def test_authenticate_user_nonexistent(self, service):
        username = 'ghost'
        password = 'Whatever'

        authenticated = await service.authenticate_user(username, password)

        assert authenticated is None
