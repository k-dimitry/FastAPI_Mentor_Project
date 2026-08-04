from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from users.services import UserService


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)