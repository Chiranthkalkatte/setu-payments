from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/setu_payments"
    SETTLEMENT_LAG_THRESHOLD_HOURS: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
