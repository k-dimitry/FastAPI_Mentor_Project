"""Response schema for POST /admin/cleanup."""

from pydantic import BaseModel


class AdminCleanupResponse(BaseModel):
    task_id: str
