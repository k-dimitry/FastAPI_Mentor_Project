from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    is_done: bool = False


class TaskOut(TaskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# For pagination
class TaskListOut(BaseModel):
    items: list[TaskOut]
    total: int
    page: int
    size: int
