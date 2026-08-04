from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class UserCreateDTO:
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    birthdate: date | None = None


@dataclass(slots=True, frozen=True)
class UserResponseDTO:
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    birthdate: date | None
    created_at: datetime
    updated_at: datetime
