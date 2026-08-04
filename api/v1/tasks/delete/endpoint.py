from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tasks.services import TaskService

from ..dependencies import get_task_service

router = APIRouter()


@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
):
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Task not found')
