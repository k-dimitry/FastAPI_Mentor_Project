import asyncio

from fastapi import APIRouter, Depends

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.dashboard.response import DashboardResponse
from api.v1.tasks.dependencies import get_task_service
from api.v1.tasks.stats.by_day.response import TaskStatsByDayResponse
from api.v1.tasks.stats.total.response import TaskStatsTotalResponse
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.get('/dashboard', response_model=DashboardResponse)
async def get_dashboard(
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Дашборд: параллельно собирает total и by_day.
    Для админа — по всем, для остальных — только свои."""
    if current_user.is_admin:
        total_coro = service.get_stats_total()
        by_day_coro = service.get_stats_by_day()
    else:
        total_coro = service.get_stats_total(current_user.id)
        by_day_coro = service.get_stats_by_day(current_user.id)

    total_dto, by_day_dto = await asyncio.gather(total_coro, by_day_coro)

    return DashboardResponse(
        total=TaskStatsTotalResponse.from_dto(total_dto),
        by_day=TaskStatsByDayResponse.from_dto(by_day_dto),
    )
