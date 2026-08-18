from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class GetListTaskQuery(BaseModel):
    page: Annotated[int, Query(1, ge=1, description='Номер страницы')] = 1
    size: Annotated[
        int, Query(20, ge=1, le=100, description='Размер страницы')
    ] = 20
