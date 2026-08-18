from uuid import UUID

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from users.dto import UserCreateDTO, UserResponseDTO
from users.exceptions import UserAlreadyExistsError
from users.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(user: User) -> UserResponseDTO:
        return UserResponseDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            birthdate=user.birthdate,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_admin=user.is_admin,
        )

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        """Регистрирует нового пользователя с хешированием пароля."""
        hashed = bcrypt.hashpw(dto.password.encode(), bcrypt.gensalt()).decode()

        user = User(
            username=dto.username,
            email=dto.email,
            first_name=dto.first_name,
            last_name=dto.last_name,
            birthdate=dto.birthdate,
            hashed_password=hashed,
        )
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise UserAlreadyExistsError(
                f"User '{dto.username}' or email '{dto.email}' already exists."
            )
        await self.db.refresh(user)
        return self._to_dto(user)

    async def get_user(self, user_id: UUID) -> UserResponseDTO | None:
        user = await self.db.get(User, user_id)
        if not user:
            return None
        return self._to_dto(user)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    async def authenticate_user(
        self, username_or_email: str, password: str
    ) -> UserResponseDTO | None:
        """Проверяет учётные данные и возвращает DTO пользователя или None."""
        # Ищем по username или email
        query = select(User).where(
            (User.username == username_or_email)
            | (User.email == username_or_email)
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return self._to_dto(user)
