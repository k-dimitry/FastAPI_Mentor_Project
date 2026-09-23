from celery import Celery
from celery.signals import worker_ready

from common.sync_db import check_sync_connection
from config import settings

celery_app = Celery(
    'fastapi_mentor',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)

celery_app.autodiscover_tasks(['notifications'], force=True)


@worker_ready.connect
def _on_worker_ready(**_kwargs) -> None:
    check_sync_connection()
