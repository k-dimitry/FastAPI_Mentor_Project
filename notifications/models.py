from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.mixins import UTCDateTime, utc_now
from database import Base

if TYPE_CHECKING:
    from users.models import User


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True,
    )
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utc_now,
        server_default=func.now(),
    )

    user: Mapped['User'] = relationship('User', back_populates='notifications')
