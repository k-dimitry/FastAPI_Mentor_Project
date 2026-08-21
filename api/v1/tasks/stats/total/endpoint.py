from fastapi import APIRouter, Depends

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.dependencies import get_task_service
from api.v1.tasks.stats.total.response import TaskStatsTotalResponse
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.get('/total', response_model=TaskStatsTotalResponse)
async def get_stats_total(
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    stats = await service.get_stats_total(user_id=current_user.id)
    return TaskStatsTotalResponse.from_dto(stats)
