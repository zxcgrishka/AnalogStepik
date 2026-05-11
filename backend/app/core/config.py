import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Analog Stepik"
    DATABASE_URL: str
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 * 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()