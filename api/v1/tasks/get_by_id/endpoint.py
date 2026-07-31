from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from tasks.models import Task

from ..common_schemas import TaskOut

router = APIRouter()


@router.get('/{task_id}', response_model=TaskOut)
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    return task
