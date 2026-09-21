from datetime import datetime
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel


class GetListTaskQuery(BaseModel):
    limit: Annotated[
        int, Query(20, ge=1, le=100, description='Количество задач на страницу')
    ] = 20
    offset: Annotated[
        int, Query(0, ge=0, description='Смещение (сколько задач пропустить)')
    ] = 0

    is_done: Annotated[
        bool | None, Query(None, description='Фильтр по статусу выполнения')
    ] = None
    created_from: Annotated[
        datetime | None,
        Query(
            None,
            description='Дата создания от (включительно)',
            json_schema_extra={'example': '2026-08-26T00:00:00Z'},
        ),
    ] = None
    created_to: Annotated[
        datetime | None,
        Query(
            None,
            description='Дата создания до (включительно)',
            json_schema_extra={'example': '2026-08-26T23:59:59Z'},
        ),
    ] = None
    query: Annotated[
        str | None,
        Query(
            None,
            min_length=1,
            max_length=100,
            description='Поиск по заголовку и описанию',
        ),
    ] = None

    order_by: Annotated[
        Literal['created_at', 'updated_at', 'title'],
        Query('created_at', description='Поле для сортировки'),
    ] = 'created_at'
    direction: Annotated[
        Literal['asc', 'desc'],
        Query('desc', description='Направление сортировки'),
    ] = 'desc'
