from fastapi import APIRouter, Depends, HTTPException, status

from users.dto import UserCreateDTO
from users.exceptions import UserAlreadyExistsError
from users.services import UserService

from ..common_schemas import UserOut
from ..dependencies import get_user_service
from .request import UserRegisterRequest

router = APIRouter()


@router.post(
    '/register', response_model=UserOut, status_code=status.HTTP_201_CREATED
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
    try:
        user_dto = await service.create_user(create_dto)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Username or email already registered.',
        )
    return UserOut.from_dto(user_dto)
