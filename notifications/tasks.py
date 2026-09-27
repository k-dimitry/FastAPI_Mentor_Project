"""Celery-задачи для notifications."""

from __future__ import annotations

import logging
from datetime import timedelta
from uuid import UUID

import sqlalchemy as sa

from celery_app import celery_app
from common.mixins import utc_now
from common.sync_db import get_sync_session
from notifications.models import Notification
from tasks.models import Task
from users.models import User

logger = logging.getLogger('app')


@celery_app.task(name='notifications.send_welcome')
def send_welcome_notification(user_id_str: str) -> str | None:
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning(
            'Invalid user_id %r, skipping welcome notification',
            user_id_str,
        )
        return None

    with get_sync_session() as session:
        try:
            user = session.get(User, user_id)
            if user is None:
                logger.warning(
                    'User %s not found, skipping welcome notification',
                    user_id_str,
                )
                return None

            notification = Notification(
                user_id=user.id,
                message=f'Welcome, {user.username}!',
            )
            session.add(notification)
            session.commit()
        except Exception:
            session.rollback()
            raise

    return str(notification.id)


@celery_app.task(name='tasks.cleanup_old')
def cleanup_old_tasks(days: int) -> int:
    if days < 1:
        raise ValueError('days must be >= 1')

    cutoff = utc_now() - timedelta(days=days)

    with get_sync_session() as session:
        try:
            result = session.execute(
                sa.delete(Task).where(
                    Task.is_done.is_(True),
                    Task.created_at < cutoff,
                )
            )
            count = result.rowcount
            session.commit()
        except Exception:
            session.rollback()
            raise

    return count
