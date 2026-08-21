from pydantic import BaseModel

from tasks.dto import TaskStatsTotalDTO


class TaskStatsTotalResponse(BaseModel):
    done_count: int
    not_done_count: int
    done_percent: float

    @classmethod
    def from_dto(cls, dto: TaskStatsTotalDTO) -> 'TaskStatsTotalResponse':
        return cls(
            done_count=dto.done_count,
            not_done_count=dto.not_done_count,
            done_percent=dto.done_percent,
        )
