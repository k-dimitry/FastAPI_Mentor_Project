from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from tasks.dto import TaskCreateDTO
from tasks.exceptions import TaskAlreadyExistsError
from tasks.services import TaskService

from ..common_schemas import TaskOut
from ..create.request import TaskCreate
from ..dependencies import get_task_service

router = APIRouter()


@router.post('/', response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
):
    create_dto = TaskCreateDTO(
        title=task_data.title,
        description=task_data.description,
    )
    try:
        result_dto = await service.create_task(create_dto, user_id=uuid4())
    except TaskAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Task with this title already exists for the user.',
        )
    return TaskOut.from_dto(result_dto)
