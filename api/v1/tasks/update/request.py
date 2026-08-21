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
            example='Обновлённое название',
        ),
    ] = None

    description: Annotated[
        str | None,
        Field(
            None,
            max_length=10_000,
            description='Новое описание задачи',
            example='Новое подробное описание',
        ),
    ] = None

    is_done: Annotated[
        bool,
        Field(
            None,
            description='Статус выполнения задачи',
            example=True,
        ),
    ] = None

    def to_dto(self) -> TaskUpdateDTO:
        return TaskUpdateDTO(**self.model_dump(exclude_unset=True))
