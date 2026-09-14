from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    DATABASE_ECHO: bool = False

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRE_MINUTES: int = 120

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Settings()
