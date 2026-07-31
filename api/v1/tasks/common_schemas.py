from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    is_done: bool = False
