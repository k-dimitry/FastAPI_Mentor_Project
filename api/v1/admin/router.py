"""Admin API router."""

from fastapi import APIRouter

from api.v1.admin.cleanup.endpoint import router as cleanup_router

router = APIRouter()
router.include_router(cleanup_router)
