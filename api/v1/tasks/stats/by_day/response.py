from datetime import date

from pydantic import BaseModel

from tasks.dto import TaskStatsByDayDTO


class TaskStatsByDayItemResponse(BaseModel):
    day: date
    total_count: int
    done_count: int
    not_done_count: int


class TaskStatsByDayResponse(BaseModel):
    items: list[TaskStatsByDayItemResponse]

    @classmethod
    def from_dto(cls, dto: TaskStatsByDayDTO) -> 'TaskStatsByDayResponse':
        return cls(
            items=[
                TaskStatsByDayItemResponse(
                    day=item.day,
                    total_count=item.total_count,
                    done_count=item.done_count,
                    not_done_count=item.not_done_count,
                )
                for item in dto.items
            ]
        )
