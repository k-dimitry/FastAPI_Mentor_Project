import logging

from fastapi import APIRouter, Depends, status

from api.v1.users.common_schemas import UserResponse
from api.v1.users.dependencies import get_user_service
from api.v1.users.register.request import UserRegisterRequest
from notifications.tasks import send_welcome_notification
from users.services import UserService

logger = logging.getLogger('app')

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
    user_dto = await service.create_user(data.to_dto())

    try:
        send_welcome_notification.delay(str(user_dto.id))
    except Exception as exc:
        logger.warning(
            'Failed to enqueue welcome notification for user %s: %s',
            user_dto.id,
            exc,
        )

    return UserResponse.from_dto(user_dto)
