"""Синхронный сервис уведомлений для Celery-воркера."""

import logging
from uuid import UUID

from common.sync_db import get_sync_session
from notifications.models import Notification
from users.models import User

logger = logging.getLogger('app')


class NotificationService:
    @staticmethod
    def send_welcome(user_id: UUID) -> str | None:
        with get_sync_session() as session:
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

        return str(notification.id)
