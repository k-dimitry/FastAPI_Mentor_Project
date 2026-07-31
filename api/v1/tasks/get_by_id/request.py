from datetime import datetime
from uuid import UUID

from api.v1.tasks.common_schemas import TaskBase


class TaskOut(TaskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
