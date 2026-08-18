from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

if TYPE_CHECKING:
    from users.dto import UserResponseDTO


class UserBase(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=50)]
    email: Annotated[EmailStr, Field(..., max_length=120)]
    first_name: Annotated[str, Field(..., min_length=1, max_length=50)]
    last_name: Annotated[str, Field(..., min_length=1, max_length=50)]
    birthdate: date | None = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_dto(cls, dto: 'UserResponseDTO') -> 'UserResponse':

        return cls(
            id=dto.id,
            username=dto.username,
            email=dto.email,
            first_name=dto.first_name,
            last_name=dto.last_name,
            birthdate=dto.birthdate,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            is_admin=dto.is_admin,
        )
