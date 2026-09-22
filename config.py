from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    DATABASE_ECHO: bool = False
    SYNC_DATABASE_URL: str = 'sqlite:///./test.db'

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRE_MINUTES: int = 120

    REDIS_URL: str = 'redis://localhost:6379/0'
    CACHE_TTL_SECONDS: int = 60
    RATE_LIMIT_N: int = 60
    RATE_LIMIT_T: int = 60
    WEB_CONCURRENCY: int = 4

    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'
    CELERY_TASK_ALWAYS_EAGER: bool = False

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
