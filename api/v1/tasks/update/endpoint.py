from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.common_schemas import TaskResponse
from api.v1.tasks.dependencies import get_task_service
from api.v1.tasks.update.request import TaskUpdateRequest
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.patch('/{task_id}', response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdateRequest,
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
    return TaskResponse.from_dto(result_dto)
