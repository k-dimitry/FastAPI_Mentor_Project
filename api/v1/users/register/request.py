from datetime import date
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, SecretStr


class UserRegisterRequest(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=50)]
    email: EmailStr
    first_name: Annotated[str, Field(..., min_length=1, max_length=50)]
    last_name: Annotated[str, Field(..., min_length=1, max_length=50)]
    password: Annotated[str, Field(..., min_length=8, max_length=128)]
    birthdate: date | None = None

    # TODO: @field_validator('password') - валидация сложности пароля + birthdate
    
