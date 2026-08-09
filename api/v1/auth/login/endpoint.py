from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.security import create_access_token
from database import get_db
from users.services import UserService

from .request import LoginRequest
from .response import TokenResponse

router = APIRouter()


@router.post('/login', response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.authenticate_user(
        data.username_or_email, data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials',
        )
    token = create_access_token(data={'sub': str(user.id)})
    return TokenResponse(access_token=token)
