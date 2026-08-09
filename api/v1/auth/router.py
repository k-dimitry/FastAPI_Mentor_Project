from fastapi import APIRouter

from .login.endpoint import router as login_router

router = APIRouter()
router.include_router(login_router)