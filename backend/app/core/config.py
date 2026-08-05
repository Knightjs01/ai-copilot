from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    debug: bool = False

    # Tenant-scoped runtime connection — a least-privilege role (no BYPASSRLS), used once a
    # request is authenticated. See app_runtime in the Phase 1 migration.
    database_url: str = "postgresql+asyncpg://app_runtime:app_runtime@localhost:5432/ai_copilot"
    # Pre-authentication connection (BYPASSRLS) — used only for looking a user up before their
    # tenant is known (login/signup by email, token-based flows). See app_auth in the migration.
    auth_database_url: str = "postgresql+asyncpg://app_auth:app_auth@localhost:5432/ai_copilot"
    # Migrations need real DDL/role-creation privileges, so they run as the bootstrap superuser —
    # deliberately a different connection than the app itself ever uses.
    migration_database_url: str = "postgresql+asyncpg://copilot:copilot@localhost:5432/ai_copilot"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:3000"
    secret_key: str = ""
    encryption_key: str = ""

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    mfa_challenge_expire_minutes: int = 10

    cookie_secure: bool = False
    frontend_base_url: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
