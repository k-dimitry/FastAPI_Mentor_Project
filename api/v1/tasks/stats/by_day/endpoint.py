from fastapi import APIRouter, Depends

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.dependencies import get_task_service
from api.v1.tasks.stats.by_day.response import TaskStatsByDayResponse
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.get('/by-day', response_model=TaskStatsByDayResponse)
async def get_stats_by_day(
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    stats = await service.get_stats_by_day(user_id=current_user.id)
    return TaskStatsByDayResponse.from_dto(stats)
