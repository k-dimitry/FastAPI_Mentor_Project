from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

UNSET = object()  # sentinel


@dataclass(slots=True, frozen=True)
class TaskResponseDTO:
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    is_done: bool = False


@dataclass(slots=True, frozen=True)
class TaskCreateDTO:
    title: str
    description: str | None = None
    is_done: bool = False


@dataclass(slots=True)
class TaskUpdateDTO:
    title: str | None | object = UNSET
    description: str | None | object = UNSET
    is_done: bool | None | object = UNSET

    @property
    def title_is_set(self):
        return self.title is not UNSET

    @property
    def description_is_set(self):
        return self.description is not UNSET

    @property
    def is_done_is_set(self):
        return self.is_done is not UNSET


@dataclass(slots=True, frozen=True)
class TaskListDTO:
    items: list[TaskResponseDTO]
    total: int
    limit: int
    offset: int


@dataclass(slots=True, frozen=True)
class TaskStatsTotalDTO:
    done_count: int
    not_done_count: int
    done_percent: float


@dataclass(slots=True, frozen=True)
class TaskStatsByDayItemDTO:
    day: date
    total_count: int
    done_count: int
    not_done_count: int


@dataclass(slots=True, frozen=True)
class TaskStatsByDayDTO:
    items: list[TaskStatsByDayItemDTO]


@dataclass(slots=True, frozen=True)
class TaskActiveUserDTO:
    user_id: UUID
    username: str
    email: str
    open_tasks: int


@dataclass(slots=True, frozen=True)
class TaskActiveUsersDTO:
    items: list[TaskActiveUserDTO]
