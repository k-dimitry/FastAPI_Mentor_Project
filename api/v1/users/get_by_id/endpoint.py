from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.auth.login.dependencies import get_current_user
from api.v1.users.common_schemas import UserResponse
from api.v1.users.dependencies import get_user_service
from users.dto import UserResponseDTO
from users.permissions import is_author_or_admin
from users.services import UserService

router = APIRouter()


@router.get('/{user_id}', response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    # Проверка прав: только автор (сам пользователь) или админ
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
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )
    return UserResponse.from_dto(user_dto)
