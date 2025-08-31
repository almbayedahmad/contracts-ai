from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_NAME: str = "contracts-ai"
    APP_VERSION: str = "0.1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_LOG_LEVEL: str = "INFO"

    DB_URL: str = "sqlite:///./contracts_ai.db"
    STORAGE_ROOT: str = "./data"
    TEMP_DIR: str = "./data/temp"
    OUTPUTS_DIR: str = "./data/outputs"

    AI_PROVIDER: str = "local"
    AI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT_SEC: int = 60

    SECRET_KEY: str = "change_me"
    ALLOWED_ORIGINS: List[AnyHttpUrl] = []

    class Config:
        env_file = ".env"

settings = Settings()
