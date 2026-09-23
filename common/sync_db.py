import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import settings

logger = logging.getLogger('app')

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autoflush=False,
)


@contextmanager
def get_sync_session() -> Iterator[Session]:
    """Context manager для sync Session — используется в Celery-тасках."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_sync_connection() -> None:
    """Проверяет connectivity sync-engine (SELECT 1)."""
    with sync_engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    logger.info(
        'Sync DB connection OK: %s',
        sync_engine.url.render_as_string(hide_password=True),
    )
