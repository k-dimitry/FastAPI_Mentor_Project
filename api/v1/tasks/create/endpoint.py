from uuid import uuid4

from fastapi import APIRouter, Depends

from tasks.dto import TaskCreateDTO
from tasks.services import TaskService

from ..common_schemas import TaskOut
from ..create.request import TaskCreate
from ..dependencies import get_task_service

router = APIRouter()


@router.post('/', response_model=TaskOut, status_code=201)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
):

    create_dto = TaskCreateDTO(
        title=task_data.title,
        description=task_data.description,
    )

    result_dto = await service.create_task(
        create_dto,
        user_id=uuid4(),
    )
    return TaskOut.model_validate(result_dto.__dict__)
