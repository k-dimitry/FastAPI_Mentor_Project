from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

_UNSET = object()  # sentinel


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
    title: str | None | object = _UNSET
    description: str | None | object = _UNSET
    is_done: bool | None | object = _UNSET

    @property
    def title_is_set(self):
        return self.title is not _UNSET

    @property
    def description_is_set(self):
        return self.description is not _UNSET

    @property
    def is_done_is_set(self):
        return self.is_done is not _UNSET


@dataclass(slots=True, frozen=True)
class TaskListDTO:
    items: list[TaskResponseDTO]
    total: int
    page: int
    size: int
