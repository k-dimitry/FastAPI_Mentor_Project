from fastapi import APIRouter

from api.v1.auth.login.endpoint import router as login_router
from api.v1.auth.token.endpoint import router as token_router

router = APIRouter()
router.include_router(login_router)
router.include_router(token_router)
