from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.params import Query

from api.v1.auth.dependencies import get_current_user
from api.v1.tasks.dependencies import get_task_service
from tasks.services import TaskService
from users.dto import UserResponseDTO

from .query import GetListTaskQuery
from .request import TaskListOut

router = APIRouter()


@router.get('/', response_model=TaskListOut)
async def get_tasks(
    request: Request,
    params: Annotated[GetListTaskQuery, Query()],
    service: TaskService = Depends(get_task_service),
    current_user: UserResponseDTO = Depends(get_current_user),
):
    result_dto = await service.get_all_tasks(
        user_id=current_user.id, page=params.page, size=params.size
    )

    next_url = None
    previous_url = None

    if params.page * params.size < result_dto.total:
        query_params = dict(request.query_params)
        query_params['page'] = str(params.page + 1)
        query_params['size'] = str(params.size)
        next_url = str(request.url.replace(query=urlencode(query_params)))

    if params.page > 1:
        query_params = dict(request.query_params)
        query_params['page'] = str(params.page - 1)
        query_params['size'] = str(params.size)
        previous_url = str(request.url.replace(query=urlencode(query_params)))

    return TaskListOut.from_dto(
        result_dto,
        next_url=next_url,
        previous_url=previous_url,
    )
