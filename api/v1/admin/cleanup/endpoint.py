"""POST /admin/cleanup — enqueue cleanup_old_tasks."""

from fastapi import APIRouter, Depends, Query

from api.v1.admin.cleanup.response import AdminCleanupResponse
from api.v1.auth.dependencies import require_admin
from notifications.tasks import cleanup_old_tasks
from users.dto import UserResponseDTO

router = APIRouter()


@router.post(
    '/cleanup',
    response_model=AdminCleanupResponse,
)
async def cleanup(
    days: int = Query(30, ge=1),
    _: UserResponseDTO = Depends(require_admin),
) -> AdminCleanupResponse:
    async_result = cleanup_old_tasks.delay(days)
    return AdminCleanupResponse(task_id=str(async_result.id))
