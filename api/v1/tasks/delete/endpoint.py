from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tasks.services import TaskService
from users.dto import UserResponseDTO

from ...auth.login.dependencies import get_current_user
from ..dependencies import get_task_service

router = APIRouter()


@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),  # ← добавили
):
    deleted = await service.delete_task(task_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Task not found',
        )
