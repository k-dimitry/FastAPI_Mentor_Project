from fastapi import APIRouter

from .login.endpoint import router as login_router
from .token.endpoint import router as token_router

router = APIRouter()
router.include_router(login_router)
router.include_router(token_router)
