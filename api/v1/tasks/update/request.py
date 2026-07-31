from api.v1.tasks.common_schemas import TaskBase


class TaskUpdate(TaskBase):
    title: str | None = None
    description: str | None = None
    is_done: bool | None = None
