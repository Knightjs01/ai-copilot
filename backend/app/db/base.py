from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base — every module's ORM models inherit from this."""


def _build_engine(database_url: str) -> AsyncEngine:
    settings = get_settings()
    # Tests run each test function on its own event loop, and pooled asyncpg connections are
    # bound to the loop that created them — reusing one across loops blows up with "attached to
    # a different loop". NullPool makes every checkout a fresh connection, sidestepping that.
    if settings.environment == "test":
        return create_async_engine(database_url, echo=settings.debug, poolclass=NullPool)
    return create_async_engine(database_url, echo=settings.debug, pool_pre_ping=True)


_settings = get_settings()

# Tenant-scoped connection (app_runtime role, no BYPASSRLS) — used once a request is
# authenticated and its company_id is known. See app/modules/auth/dependencies.get_tenant_db.
engine = _build_engine(_settings.database_url)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# Pre-authentication connection (app_auth role, BYPASSRLS) — used only for the specific flows
# that must look a user up before their tenant is known: login/signup by email, and token-based
# flows (refresh, verify-email, forgot/reset-password, accept-invite) where the random token
# itself — not company context — is the proof of authorization. Its table grants are the same as
# app_runtime's; BYPASSRLS only matters in practice because it's the one role permitted to read
# `users` without an app.current_company_id set. See app/db/session.get_db.
auth_engine = _build_engine(_settings.auth_database_url)
auth_session_factory = async_sessionmaker(auth_engine, expire_on_commit=False)
