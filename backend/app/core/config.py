from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://copilot:copilot@localhost:5432/ai_copilot"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:3000"
    secret_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
