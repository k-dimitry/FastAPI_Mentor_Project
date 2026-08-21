from fastapi import APIRouter, Depends

from api.v1.users.common_schemas import UserResponse
from api.v1.users.dependencies import get_user_with_access_check
from users.dto import UserResponseDTO

router = APIRouter()


@router.get('/{user_id}', response_model=UserResponse)
async def get_user(
    user_dto: UserResponseDTO = Depends(get_user_with_access_check),
):
    # user_id передаётся в get_user_with_access_check через путь автоматически.
    return UserResponse.from_dto(user_dto)
