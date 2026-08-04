from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from users.services import UserService

from ..common_schemas import UserOut
from ..dependencies import get_user_service

router = APIRouter()


@router.get('/{user_id}', response_model=UserOut)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
):
    user_dto = await service.get_user(user_id)
    if user_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )
    return UserOut.from_dto(user_dto)
