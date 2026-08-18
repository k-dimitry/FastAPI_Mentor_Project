from pydantic import BaseModel

from api.v1.tasks.common_schemas import TaskOut


class TaskListOut(BaseModel):
    result: list[TaskOut]
    count: int
    next: str | None
    previous: str | None

    @classmethod
    def from_dto(
        cls,
        dto: 'TaskListDTO',
        next_url: str | None = None,
        previous_url: str | None = None,
    ) -> 'TaskListOut':

        return cls(
            result=[TaskOut.from_dto(item) for item in dto.items],
            count=dto.total,
            next=next_url,
            previous=previous_url,
        )
