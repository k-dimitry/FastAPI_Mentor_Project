from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from users.models import User


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_done: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE')
    )

    author: Mapped['User'] = relationship('User', back_populates='tasks')

    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='unique_user_task_title'),
    )
