"""Celery-задачи для notifications."""

from uuid import UUID

from celery_app import celery_app
from notifications.services import NotificationService
from tasks.services import TaskCleanupService


@celery_app.task(name='notifications.send_welcome')
def send_welcome_notification(user_id: UUID) -> str | None:
    return NotificationService.send_welcome(user_id)


@celery_app.task(name='tasks.cleanup_old')
def cleanup_old_tasks(days: int) -> int:
    return TaskCleanupService.delete_old_done(days)
