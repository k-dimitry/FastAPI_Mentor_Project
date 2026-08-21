from fastapi import APIRouter

from api.v1.tasks.stats.by_day.endpoint import router as by_day_router
from api.v1.tasks.stats.total.endpoint import router as total_router

router = APIRouter()
router.include_router(total_router)
router.include_router(by_day_router)
