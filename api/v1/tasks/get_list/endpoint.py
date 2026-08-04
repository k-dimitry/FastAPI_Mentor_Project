from fastapi import APIRouter, Depends

from tasks.services import TaskService

from ..dependencies import get_task_service
from .query import PaginationParams
from .request import TaskListOut

router = APIRouter()


@router.get('/', response_model=TaskListOut)
async def get_tasks(
    params: PaginationParams = Depends(),
    service: TaskService = Depends(get_task_service),
):
    result_dto = await service.get_all_tasks(page=params.page, size=params.size)
    return TaskListOut.from_dto(result_dto)
