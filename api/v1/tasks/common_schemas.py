from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: Annotated[str, Field(..., max_length=50)]
    description: Annotated[str, Field(None, max_length=10_000)]
    is_done: bool = False


class TaskOut(TaskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_dto(cls, dto: 'TaskResponseDTO') -> 'TaskOut':
        # Import here to avoid cycle import
        from tasks.dto import TaskResponseDTO

        return cls(
            id=dto.id,
            title=dto.title,
            description=dto.description,
            is_done=dto.is_done,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
