import logging

from fastapi import status
from httpx import AsyncClient


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class TestRequestLogging:
    async def test_info_does_not_log_bodies(
        self, client: AsyncClient, user_token
    ):
        app_logger = logging.getLogger('app')
        assert app_logger.getEffectiveLevel() == logging.INFO

        handler = _ListHandler()
        app_logger.addHandler(handler)
        try:
            response = await client.post(
                '/api/v1/tasks/',
                headers={'Authorization': f'Bearer {user_token}'},
                json={'title': 'Visible task', 'description': 'private note'},
            )
        finally:
            app_logger.removeHandler(handler)

        assert response.status_code == status.HTTP_201_CREATED
        messages = [record.getMessage() for record in handler.records]
        assert any(
            message.startswith('POST /api/v1/tasks/') for message in messages
        )
        assert not any(
            'Request body' in message or 'Response body' in message
            for message in messages
        )
        assert 'private note' not in ' '.join(messages)
        assert all(record.levelno >= logging.INFO for record in handler.records)
