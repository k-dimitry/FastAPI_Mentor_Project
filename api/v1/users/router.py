from fastapi import APIRouter

from api.v1.users.get_by_id.endpoint import router as get_by_id_router
from api.v1.users.register.endpoint import router as register_router

router = APIRouter()
router.include_router(register_router)
router.include_router(get_by_id_router)