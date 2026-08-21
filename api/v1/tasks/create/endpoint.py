from fastapi import APIRouter, Depends, status

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.common_schemas import TaskResponse
from api.v1.tasks.create.request import TaskCreate
from api.v1.tasks.dependencies import get_task_service
from tasks.dto import TaskCreateDTO
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.post(
    '/', response_model=TaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    create_dto = TaskCreateDTO(
        title=task_data.title,
        description=task_data.description,
        is_done=task_data.is_done,
    )
    result_dto = await service.create_task(create_dto, user_id=current_user.id)
    return TaskResponse.from_dto(result_dto)
