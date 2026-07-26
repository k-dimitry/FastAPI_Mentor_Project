from fastapi import APIRouter

from .tasks.router import router as tasks_router

router = APIRouter()

router.include_router(tasks_router, prefix='/tasks', tags=['Tasks'])
