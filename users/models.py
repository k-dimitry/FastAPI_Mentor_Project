from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.mixins import TimestampMixin
from database import Base

if TYPE_CHECKING:
    from tasks.models import Task


class User(TimestampMixin, Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)
    # TODO: encrypted
    hashed_password: Mapped[str] = mapped_column(String(255))
    tasks: Mapped[list['Task']] = relationship('Task', back_populates='user')
