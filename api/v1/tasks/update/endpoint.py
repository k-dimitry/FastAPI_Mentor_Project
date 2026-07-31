from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from tasks.models import Task

from ..get_by_id.request import TaskOut
from .request import TaskUpdate

router = APIRouter()


@router.put('/{task_id}', response_model=TaskOut)
async def update_task(
    task_id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')

    # Обновляем только переданные поля
    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task
