from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth.dependencies import get_current_user
from database import get_db
from users.dto import UserResponseDTO
from users.permissions import is_author_or_admin
from users.services import UserService


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


async def get_user_with_access_check(
    user_id: UUID = Path(..., description='ID пользователя'),
    service: UserService = Depends(get_user_service),
    current_user: UserResponseDTO = Depends(get_current_user),
) -> UserResponseDTO:
    """Проверяет права доступа и возвращает запрашиваемого пользователя."""
    # Только автор (сам пользователь) или администратор
    if not is_author_or_admin(
        current_user_id=current_user.id,
        target_user_id=user_id,
        is_admin=current_user.is_admin,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not enough permissions to view this user',
        )

    user_dto = await service.get_user(user_id)
    if user_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )
    return user_dto
