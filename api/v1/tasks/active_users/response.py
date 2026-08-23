from uuid import UUID

from pydantic import BaseModel

from tasks.dto import TaskActiveUsersDTO


class TaskActiveUserResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    open_tasks: int


class TaskActiveUsersResponse(BaseModel):
    items: list[TaskActiveUserResponse]

    @classmethod
    def from_dto(cls, dto: TaskActiveUsersDTO) -> 'TaskActiveUsersResponse':
        return cls(
            items=[
                TaskActiveUserResponse(
                    user_id=item.user_id,
                    username=item.username,
                    email=item.email,
                    open_tasks=item.open_tasks,
                )
                for item in dto.items
            ]
        )
