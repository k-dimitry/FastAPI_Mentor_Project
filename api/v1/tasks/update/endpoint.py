from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.auth.dependencies import get_current_user
from tasks.services import TaskService
from users.dto import UserResponseDTO

from ..common_schemas import TaskOut
from ..dependencies import get_task_service
from ..update.request import TaskUpdate

router = APIRouter()


@router.patch('/{task_id}', response_model=TaskOut)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    update_dto = task_data.to_dto()
    result_dto = await service.update_task(
        task_id, update_dto, user_id=current_user.id
    )
    if result_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Task not found',
        )
    return TaskOut.from_dto(result_dto)
