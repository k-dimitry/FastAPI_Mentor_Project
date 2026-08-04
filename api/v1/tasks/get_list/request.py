from pydantic import BaseModel

from ..common_schemas import TaskOut


class TaskListOut(BaseModel):
    items: list[TaskOut]
    total: int
    page: int
    size: int

    @classmethod
    def from_dto(cls, dto: 'TaskListDTO') -> 'TaskListOut':
        # Import here to avoid cycle import
        from tasks.dto import TaskListDTO

        return cls(
            items=[TaskOut.from_dto(item) for item in dto.items],
            total=dto.total,
            page=dto.page,
            size=dto.size,
        )
