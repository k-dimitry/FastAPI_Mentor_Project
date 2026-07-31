from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


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
    title: str | None = None
    description: str | None = None
    is_done: bool | None = None


@dataclass(slots=True, frozen=True)
class TaskListDTO:
    items: list[TaskResponseDTO]
    total: int
    page: int
    size: int
