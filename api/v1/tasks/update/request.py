from ..common_schemas import TaskBase


class TaskUpdate(TaskBase):
    title: str | None = None
    description: str | None = None
    is_done: bool | None = None

    # TODO: to_dto method and validation
    # examples, descriptions for docs
