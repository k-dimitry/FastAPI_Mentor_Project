from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.params import Query

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.dependencies import get_task_service
from api.v1.tasks.get_list.query import GetListTaskQuery
from api.v1.tasks.get_list.request import TaskListResponse
from common.pagination import get_pagination_urls
from tasks.services import TaskService
from users.dto import UserResponseDTO

router = APIRouter()


@router.get('/', response_model=TaskListResponse)
async def get_tasks(
    request: Request,
    params: Annotated[GetListTaskQuery, Query()],
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    result_dto = await service.get_all_tasks(
        user_id=current_user.id, page=params.page, size=params.size
    )

    next_url, previous_url = get_pagination_urls(
        request=request,
        page=params.page,
        size=params.size,
        total=result_dto.total,
    )

    return TaskListResponse.from_dto(
        result_dto,
        next_url=next_url,
        previous_url=previous_url,
    )
