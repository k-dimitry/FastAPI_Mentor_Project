from fastapi import APIRouter

from api.v1.tasks.active_users.endpoint import router as active_users_router
from api.v1.tasks.create.endpoint import router as create_router
from api.v1.tasks.dashboard.endpoint import router as dashboard_router
from api.v1.tasks.delete.endpoint import router as delete_router
from api.v1.tasks.get_by_id.endpoint import router as get_by_id_router
from api.v1.tasks.get_list.endpoint import router as get_list_router
from api.v1.tasks.stats.router import router as stats_router
from api.v1.tasks.update.endpoint import router as updated_router

router = APIRouter()

router.include_router(create_router)
router.include_router(delete_router)
router.include_router(active_users_router)
router.include_router(dashboard_router)
router.include_router(get_by_id_router)
router.include_router(get_list_router)
router.include_router(updated_router)


router.include_router(stats_router, prefix='/stats', tags=['Task Stats'])
