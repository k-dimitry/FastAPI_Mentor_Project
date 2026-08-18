from typing import Annotated

from pydantic import BaseModel, Field

from tasks.dto import _UNSET, TaskUpdateDTO


class TaskUpdate(BaseModel):
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
        provided = self.model_fields_set
        return TaskUpdateDTO(
            title=self.title if 'title' in provided else _UNSET,
            description=self.description
            if 'description' in provided
            else _UNSET,
            is_done=self.is_done if 'is_done' in provided else _UNSET,
        )
