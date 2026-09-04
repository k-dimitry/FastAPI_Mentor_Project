import pytest

from users.dto import UserCreateDTO
from users.exceptions import UserAlreadyExistsError
from users.models import User
from users.services import UserService

pytestmark = pytest.mark.asyncio


class TestUserService:
    @pytest.fixture
    async def service(self, db_session):
        return UserService(db_session)

    async def test_create_user(self, service):
        dto = UserCreateDTO(
            username='newuser',
            email='new@example.com',
            first_name='New',
            last_name='User',
            password='Str0ngPass!',
            birthdate=None,
        )
        result = await service.create_user(dto)
        assert result.username == 'newuser'
        assert result.email == 'new@example.com'
        assert result.first_name == 'New'
        assert result.last_name == 'User'
        assert result.is_admin is False

        user_in_db = await service.db.get(User, result.id)
        assert user_in_db is not None
        # Пароль не должен совпадать с исходным (захэширован)
        assert user_in_db.hashed_password != 'Str0ngPass!'
        assert len(user_in_db.hashed_password) > 20

    async def test_create_duplicate_user(self, service):
        dto = UserCreateDTO(
            username='duplicate',
            email='dup@example.com',
            first_name='Dup',
            last_name='User',
            password='Str0ngPass!',
            birthdate=None,
        )
        await service.create_user(dto)
        with pytest.raises(UserAlreadyExistsError):
            await service.create_user(dto)

    async def test_authenticate_user_success(self, service):
        await service.create_user(
            UserCreateDTO(
                username='authuser',
                email='auth@example.com',
                first_name='Auth',
                last_name='User',
                password='Str0ngPass!',
                birthdate=None,
            )
        )
        authenticated = await service.authenticate_user(
            'authuser', 'Str0ngPass!'
        )
        assert authenticated is not None
        assert authenticated.username == 'authuser'

    async def test_authenticate_user_wrong_password(self, service):
        await service.create_user(
            UserCreateDTO(
                username='authuser2',
                email='auth2@example.com',
                first_name='Auth',
                last_name='User',
                password='Str0ngPass!',
                birthdate=None,
            )
        )
        authenticated = await service.authenticate_user(
            'authuser2', 'WrongPass'
        )
        assert authenticated is None

    async def test_authenticate_user_nonexistent(self, service):
        authenticated = await service.authenticate_user('ghost', 'Whatever')
        assert authenticated is None
