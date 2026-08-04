from fastapi import APIRouter

from .tasks.router import router as tasks_router
from .users.router import router as users_router

router = APIRouter(prefix='/v1')

router.include_router(tasks_router, prefix='/tasks', tags=['Tasks'])
router.include_router(users_router, prefix='/users', tags=['Users'])