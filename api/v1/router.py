from fastapi import APIRouter

from api.v1.auth.router import router as auth_router
from api.v1.tasks.router import router as tasks_router
from api.v1.users.router import router as users_router

router = APIRouter(prefix='/v1')

router.include_router(tasks_router, prefix='/tasks', tags=['Tasks'])
router.include_router(users_router, prefix='/users', tags=['Users'])
router.include_router(auth_router, prefix='/auth', tags=['Auth'])
