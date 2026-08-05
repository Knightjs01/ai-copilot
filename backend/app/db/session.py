from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import auth_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Pre-authentication session (app_auth role) — for flows that look a user up before their
    tenant is known (signup/login by email, token-based flows). Authenticated, tenant-scoped
    routes should use app.modules.auth.dependencies.get_tenant_db instead."""

    async with auth_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
