from fastapi import APIRouter

from .get_by_id.endpoint import router as get_by_id_router
from .register.endpoint import router as register_router

router = APIRouter()
router.include_router(register_router)
router.include_router(get_by_id_router)