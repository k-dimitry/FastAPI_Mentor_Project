from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class UserCreateDTO:
    username: str
    email: str
    first_name: str
    last_name: str
    password: str = field(repr=False)
    birthdate: date | None = field(repr=False, default=None)


@dataclass(slots=True, frozen=True)
class UserResponseDTO:
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime
    birthdate: date | None = field(repr=False)
    is_admin: bool = False
