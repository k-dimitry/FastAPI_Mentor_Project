from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tasks.services import TaskService
from users.dto import UserResponseDTO

from ...auth.login.dependencies import get_current_user
from ..common_schemas import TaskOut
from ..dependencies import get_task_service

router = APIRouter()


@router.get('/{task_id}', response_model=TaskOut)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    task_dto = await service.get_task(task_id, user_id=current_user.id)
    if task_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Task not found',
        )
    return TaskOut.from_dto(task_dto)
