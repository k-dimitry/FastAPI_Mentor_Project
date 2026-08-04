from uuid import UUID

import bcrypt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .dto import UserCreateDTO, UserResponseDTO
from .exceptions import UserAlreadyExistsError
from .models import User


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
