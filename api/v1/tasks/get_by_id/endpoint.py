from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from tasks.services import TaskService

from ..common_schemas import TaskOut
from ..dependencies import get_task_service

router = APIRouter()


@router.get('/{task_id}', response_model=TaskOut)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
):
    task_dto = await service.get_task(task_id)
    if task_dto is None:
        raise HTTPException(status_code=404, detail='Task not found')
    return TaskOut.model_validate(task_dto.__dict__)
