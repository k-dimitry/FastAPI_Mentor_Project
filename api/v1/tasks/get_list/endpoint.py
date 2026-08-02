from fastapi import APIRouter, Depends, Query

from tasks.services import TaskService

from ..common_schemas import TaskListOut, TaskOut
from ..dependencies import get_task_service

router = APIRouter()


@router.get('/', response_model=TaskListOut)
async def get_tasks(
    page: int = Query(1, ge=1, description='Page number, starting from 1'),
    size: int = Query(
        20, ge=1, le=100, description='Number of Tasks on a page'
    ),
    service: TaskService = Depends(get_task_service),
):
    result_dto = await service.get_all_tasks(page=page, size=size)

    items_pydantic = [
        TaskOut.model_validate(item.__dict__) for item in result_dto.items
    ]
    return TaskListOut(
        items=items_pydantic,
        total=result_dto.total,
        page=result_dto.page,
        size=result_dto.size,
    )
