from fastapi import APIRouter, Depends

from tasks.services import TaskService
from users.dto import UserResponseDTO

from ...auth.login.dependencies import get_current_user
from ..dependencies import get_task_service
from .query import PaginationParams
from .request import TaskListOut

router = APIRouter()


@router.get('/', response_model=TaskListOut)
async def get_tasks(
    params: PaginationParams = Depends(),
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    result_dto = await service.get_all_tasks(
        user_id=current_user.id, page=params.page, size=params.size
    )
    return TaskListOut.from_dto(result_dto)
