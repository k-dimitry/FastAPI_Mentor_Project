from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    is_done: bool = False


class TaskCreate(TaskBase):
    pass


class TaskOut(TaskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskUpdate(TaskBase):
    title: str | None = None
    description: str | None = None
    is_done: bool | None = None
