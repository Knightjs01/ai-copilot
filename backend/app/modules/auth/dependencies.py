import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any, NamedTuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.base import async_session_factory
from app.modules.auth import security
from app.modules.auth.email import BrevoEmailSender, ConsoleEmailSender, EmailSender
from app.modules.auth.models import User
from app.modules.auth.repository.roles import RoleRepository
from app.modules.auth.repository.users import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)
_default_email_sender: EmailSender | None = None


def get_email_sender() -> EmailSender:
    """Overridable via app.dependency_overrides — tests inject a capturing sender instead of
    letting emails just go to logs, so they can read the verification/reset/invite tokens.

    Constructed lazily, not at module import time, matching the pattern in e.g.
    app/modules/intelligence/dependencies.py — picks BrevoEmailSender once BREVO_API_KEY is set
    (production), otherwise ConsoleEmailSender (local dev / CI, where it's never set)."""

    global _default_email_sender
    if _default_email_sender is None:
        settings = get_settings()
        if settings.brevo_api_key:
            _default_email_sender = BrevoEmailSender(
                api_key=settings.brevo_api_key, sender_email=settings.brevo_sender_email
            )
        else:
            _default_email_sender = ConsoleEmailSender()
    return _default_email_sender


class CurrentUser(NamedTuple):
    id: uuid.UUID
    company_id: uuid.UUID
    email: str
    permissions: set[str]


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return credentials.credentials


async def get_token_payload(token: str = Depends(get_bearer_token)) -> dict[str, Any]:
    try:
        return security.decode_access_token(token)
    except security.TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc


async def get_tenant_db(
    payload: dict[str, Any] = Depends(get_token_payload),
) -> AsyncGenerator[AsyncSession, None]:
    """Request-scoped session with the tenant-isolation RLS variable set for its whole
    transaction. SET LOCAL is transaction-scoped — it stays in effect because this session's
    implicit transaction spans the whole request (no commit happens until the end)."""

    # Postgres's SET LOCAL does not accept bind parameters ($1) — it needs a literal in the SQL
    # text. Validating as a UUID first (raises on anything malformed) makes interpolating it safe:
    # a parsed UUID can only stringify back to hex-and-dashes, nothing SQL-syntax-relevant.
    company_id = uuid.UUID(payload["company_id"])

    async with async_session_factory() as session:
        try:
            await session.execute(text(f"SET LOCAL app.current_company_id = '{company_id}'"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user_model(
    payload: dict[str, Any] = Depends(get_token_payload),
    session: AsyncSession = Depends(get_tenant_db),
) -> User:
    """The authenticated ORM User row — use this when a route needs to mutate the user.
    FastAPI caches this per-request, so get_current_user (below) reuses the same query."""

    user = await UserRepository(session).get_by_id(uuid.UUID(payload["sub"]))
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    if str(user.company_id) != payload["company_id"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token/company mismatch"
        )
    return user


async def get_current_user(
    user: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> CurrentUser:
    """Lightweight, permission-bearing view of the authenticated user — use this when a route
    only needs to check identity/permissions, not mutate the user row."""

    permission_codes = await RoleRepository(session).get_permission_codes_for_user(user.id)
    return CurrentUser(
        id=user.id, company_id=user.company_id, email=user.email, permissions=permission_codes
    )


def require_permission(code: str) -> Callable[..., Awaitable[CurrentUser]]:
    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if code not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return checker
