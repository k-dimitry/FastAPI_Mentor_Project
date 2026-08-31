from typing import Annotated

from pydantic import BaseModel, Field

from tasks.dto import UNSET, TaskUpdateDTO


class TaskUpdateRequest(BaseModel):
    title: Annotated[
        str,
        Field(
            None,
            max_length=50,
            description='Новый заголовок задачи',
            json_schema_extra={'example': 'Обновлённое название'},
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            None,
            max_length=10_000,
            description='Новое описание задачи',
            json_schema_extra={'example': 'Новое подробное описание'},
        ),
    ] = None

    is_done: Annotated[
        bool,
        Field(
            None,
            description='Статус выполнения задачи',
            json_schema_extra={'example': True},
        ),
    ] = None

    def to_dto(self) -> TaskUpdateDTO:
        return TaskUpdateDTO(**self.model_dump(exclude_unset=True))
