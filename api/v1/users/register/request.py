import re
from datetime import date
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class UserRegisterRequest(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=50)]
    email: EmailStr
    first_name: Annotated[str, Field(..., min_length=1, max_length=50)]
    last_name: Annotated[str, Field(..., min_length=1, max_length=50)]
    password: Annotated[SecretStr, Field(..., min_length=8, max_length=128)]
    birthdate: date | None = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        """
        Пароль должен содержать:
        - минимум одну заглавную букву (A-Z)
        - минимум одну строчную букву (a-z)
        - минимум одну цифру (0-9)
        - минимум один специальный символ (!@#$%^&*)
        """
        password = v.get_secret_value()
        if not re.search(r'[A-Z]', password):
            raise ValueError(
                'Пароль должен содержать хотя бы одну заглавную букву'
            )
        if not re.search(r'[a-z]', password):
            raise ValueError(
                'Пароль должен содержать хотя бы одну строчную букву'
            )
        if not re.search(r'\d', password):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[!@#$%^&*]', password):
            raise ValueError(
                'Пароль должен содержать '
                'хотя бы один специальный символ (!@#$%^&*)'
            )
        return v

    @field_validator('birthdate')
    @classmethod
    def validate_birthdate(cls, v: date | None) -> date | None:
        if v is not None:
            if v > date.today():
                raise ValueError('Дата рождения не может быть в будущем')
            if v.year < 1900:
                raise ValueError('Дата рождения не может быть раньше 1900 года')
        return v
