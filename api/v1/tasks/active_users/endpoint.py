from fastapi import APIRouter, Depends

from api.v1.auth.dependencies import require_admin
from api.v1.tasks.active_users.response import TaskActiveUsersResponse
from api.v1.tasks.dependencies import get_task_service
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.get('/active-users', response_model=TaskActiveUsersResponse)
async def get_active_users(
    service: TaskService = Depends(get_task_service),
    _: UserResponseDTO = Depends(require_admin),
):
    dto = await service.get_active_users(limit=10)
    return TaskActiveUsersResponse.from_dto(dto)
