class AlreadyExistsError(Exception):
    """Конфликт: ресурс уже существует."""

    def __init__(self, message: str = 'Resource already exists'):
        self.message = message
        super().__init__(message)
