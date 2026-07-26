from fastapi import APIRouter

from .create.endpoint import router as create_router
from .delete.endpoint import router as delete_router
from .get_by_id.endpoint import router as get_by_id_router
from .get_list.endpoint import router as get_list_router
from .update.endpoint import router as updated_router

router = APIRouter()

router.include_router(get_list_router)
router.include_router(get_by_id_router)
router.include_router(create_router)
router.include_router(delete_router)
router.include_router(updated_router)
