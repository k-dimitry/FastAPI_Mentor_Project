"""Синхронный сервис уведомлений для Celery-воркера."""

import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from common.sync_db import get_sync_session
from notifications.models import Notification
from users.models import User

logger = logging.getLogger('app')


class NotificationService:
    @staticmethod
    def send_welcome(user_id: UUID) -> str | None:
        if not isinstance(user_id, UUID):
            user_id = UUID(str(user_id))

        with get_sync_session() as session:
            try:
                user = session.get(User, user_id)
                if user is None:
                    logger.warning(
                        'User %s not found, skipping welcome notification',
                        user_id,
                    )
                    return None

                notification = Notification(
                    user_id=user.id,
                    message=f'Welcome, {user.username}!',
                )
                session.add(notification)
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise

        return str(notification.id)
