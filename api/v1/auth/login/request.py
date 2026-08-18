from typing import Annotated

from pydantic import BaseModel, Field, SecretStr


class LoginRequest(BaseModel):
    username_or_email: Annotated[
        str,
        Field(
            ...,
            min_length=3,
            max_length=120,
            description='Username or email',
        ),
    ]
    password: Annotated[SecretStr, Field(..., min_length=8)]
