from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from tasks.models import Task

from ..create.request import TaskCreate
from ..get_by_id.request import TaskOut

router = APIRouter()


@router.post('/', response_model=TaskOut, status_code=201)
async def create_task(
    task_data: TaskCreate, db: AsyncSession = Depends(get_db)
):
    new_task = Task(**task_data.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task
