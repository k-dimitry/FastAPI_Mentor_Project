from fastapi import APIRouter, Depends

from tasks.services import TaskService

from ..common_schemas import TaskOut
from ..dependencies import get_task_service

router = APIRouter()


@router.get('/', response_model=list[TaskOut])
async def get_tasks(
    service: TaskService = Depends(get_task_service),
):
    dtos = await service.get_all_tasks()
    return [TaskOut.model_validate(dto.__dict__) for dto in dtos]
