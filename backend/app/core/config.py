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
    # "Mandatory from day one" MFA, but a grace path rather than an instant lockout on
    # signup — see app/modules/auth/mfa_policy.py. A brand-new account can use the product
    # normally for this many days before every business-logic route starts requiring MFA
    # enrollment (auth/me and the mfa/* endpoints themselves are always reachable, so an
    # account can never be locked out of enrolling).
    mfa_grace_period_days: int = 7

    # WebAuthn/passkey relying party config — see app/core/webauthn.py. rp_id must be the bare
    # domain (no scheme/port) and must match (or be a registrable suffix of) the origin the
    # frontend is actually served from, or every ceremony will fail browser-side; "localhost"/
    # http://localhost:3000 is the only combination that works without HTTPS, which is why local
    # dev defaults to it even though the values look inconsistent with cookie_secure=false prod.
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Phantom Hire"
    webauthn_origin: str = "http://localhost:3000"
    webauthn_challenge_expire_seconds: int = 300
    # Step-up auth (see app/modules/auth/dependencies.py:require_step_up) — how long a
    # freshly-verified password+MFA assertion stays valid for gating a single high-risk action
    # (identity reveal, project purge, admin invite). Short and single-purpose on purpose: this
    # is not a session, it's proof of "the person at the keyboard right now" for one action.
    step_up_token_expire_minutes: int = 5

    cookie_secure: bool = False
    frontend_base_url: str = "http://localhost:3000"

    # Local-filesystem resume storage — see app/modules/candidates/storage.py. Swap for an
    # S3-backed FileStorage implementation before deploying anywhere with more than one instance.
    storage_dir: str = "/app/storage"
    max_resume_size_mb: int = 10
    max_media_size_mb: int = 5

    # No default on purpose, same as secret_key — must be set for real use. See
    # app/modules/intelligence/llm_client.py. Never populated by app code; the user sets it
    # directly in backend/.env.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # No default on purpose, same as anthropic_api_key. Empty means app.modules.auth.dependencies
    # .get_email_sender() falls back to ConsoleEmailSender (local dev / tests) — see
    # app/modules/auth/email.py's BrevoEmailSender for how this is used once set.
    brevo_api_key: str = ""
    brevo_sender_email: str = ""

    # No default on purpose, same as anthropic_api_key. Empty means
    # app.modules.geocoding.service.GeocodingService.autocomplete degrades to returning no
    # suggestions (the location field still accepts free-typed text) rather than erroring — local
    # dev without this key set is never blocked.
    geoapify_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
