from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tasks.dto import TaskUpdateDTO
from tasks.services import TaskService

from ..common_schemas import TaskOut
from ..dependencies import get_task_service
from ..update.request import TaskUpdate

router = APIRouter()


@router.patch('/{task_id}', response_model=TaskOut)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    update_dto = TaskUpdateDTO(
        title=task_data.title,
        description=task_data.description,
        is_done=task_data.is_done,
    )
    result_dto = await service.update_task(task_id, update_dto)
    if result_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Task not found',
        )
    return TaskOut.from_dto(result_dto)
