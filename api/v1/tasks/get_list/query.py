from datetime import datetime
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel


class GetListTaskQuery(BaseModel):
    # Пагинация limit/offset вместо page/size
    limit: Annotated[
        int, Query(20, ge=1, le=100, description='Количество задач на страницу')
    ] = 20
    offset: Annotated[
        int, Query(0, ge=0, description='Смещение (сколько задач пропустить)')
    ] = 0

    # Фильтры
    is_done: Annotated[
        bool | None, Query(None, description='Фильтр по статусу выполнения')
    ] = None
    created_from: Annotated[
        datetime | None,
        Query(
            None,
            description='Дата создания от (включительно)',
            examples=['2026-08-18T07:08:05.241538Z'],
        ),
    ] = None
    created_to: Annotated[
        datetime | None,
        Query(
            None,
            description='Дата создания до (включительно)',
            examples=['2026-08-19T07:08:05.241538Z'],
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

    # Сортировка
    order_by: Annotated[
        Literal['created_at', 'updated_at', 'title'],
        Query('created_at', description='Поле для сортировки'),
    ] = 'created_at'
    direction: Annotated[
        Literal['asc', 'desc'],
        Query('desc', description='Направление сортировки'),
    ] = 'desc'
