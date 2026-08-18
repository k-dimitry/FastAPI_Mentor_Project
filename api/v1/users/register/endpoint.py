from fastapi import APIRouter, Depends, status

from api.v1.users.common_schemas import UserResponse
from api.v1.users.dependencies import get_user_service
from api.v1.users.register.request import UserRegisterRequest
from users.dto import UserCreateDTO
from users.services import UserService

router = APIRouter()


@router.post(
    '/register',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserRegisterRequest,
    service: UserService = Depends(get_user_service),
):
    create_dto = UserCreateDTO(
        username=data.username,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
        birthdate=data.birthdate,
    )
    user_dto = await service.create_user(create_dto)
    return UserResponse.from_dto(user_dto)
