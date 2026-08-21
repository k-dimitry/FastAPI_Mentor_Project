from dataclasses import dataclass
from datetime import datetime
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
