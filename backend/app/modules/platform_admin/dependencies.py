import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any, NamedTuple

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import maintenance_session_factory
from app.db.session import get_db
from app.modules.auth import security
from app.modules.auth.dependencies import get_bearer_token
from app.modules.platform_admin.models import PlatformAdmin
from app.modules.platform_admin.repository import PlatformAdminRepository
from app.modules.platform_admin.role_repository import PlatformAdminRoleRepository


async def get_platform_admin_token_payload(
    token: str = Depends(get_bearer_token),
) -> dict[str, Any]:
    try:
        payload = security.decode_access_token(token)
    except security.TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc
    if payload.get("scope") != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return payload


async def require_platform_admin(
    payload: dict[str, Any] = Depends(get_platform_admin_token_payload),
    # No tenant to scope RLS by -- platform_admins isn't tenant-owned data, same reasoning as
    # candidate_auth.dependencies.get_current_candidate's use of get_db.
    session: AsyncSession = Depends(get_db),
) -> PlatformAdmin:
    admin = await PlatformAdminRepository(session).get_by_id(uuid.UUID(payload["sub"]))
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return admin


async def require_platform_admin_step_up(
    x_step_up_token: str | None = Header(default=None, alias="X-Step-Up-Token"),
    admin: PlatformAdmin = Depends(require_platform_admin),
) -> PlatformAdmin:
    """Gate for the highest-risk platform-admin actions (Danger Zone) -- see
    security.create_platform_admin_step_up_token. Unlike auth.dependencies.require_step_up
    (built on require_mfa_enrolled, which allows company users a grace period), there is no
    grace period here: an admin who hasn't enrolled MFA at all is refused outright, not
    fallen back to a password-only check, per the explicit requirement that Danger Zone must be
    unreachable without MFA from day one. Callers get a token from POST /platform-admin/step-up
    (which re-checks password, and MFA code since MFA is mandatory for this path) and pass it
    back as the X-Step-Up-Token header on the actual request."""

    if not admin.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Set up multi-factor authentication before accessing this.",
        )
    if x_step_up_token is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Step-up verification required for this action. "
                "Call POST /platform-admin/step-up first and retry with an "
                "X-Step-Up-Token header."
            ),
        )
    try:
        payload = security.decode_platform_admin_step_up_token(x_step_up_token)
    except security.TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up verification required for this action.",
        ) from exc
    if payload.get("sub") != str(admin.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Step-up verification required for this action.",
        )
    return admin


class PlatformAdminContext(NamedTuple):
    """Lightweight, permission-bearing view of the authenticated admin -- mirrors
    auth.dependencies.CurrentUser exactly. Use this when a route only needs to check
    identity/permissions, not mutate the PlatformAdmin row."""

    id: uuid.UUID
    email: str
    full_name: str
    roles: list[str]
    permissions: set[str]
    mfa_enabled: bool


async def get_current_platform_admin(
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> PlatformAdminContext:
    role_repo = PlatformAdminRoleRepository(session)
    roles = await role_repo.get_roles_for_admin(admin.id)
    permission_codes = await role_repo.get_permission_codes_for_admin(admin.id)
    return PlatformAdminContext(
        id=admin.id,
        email=admin.email,
        full_name=admin.full_name,
        roles=[role.name for role in roles],
        permissions=permission_codes,
        mfa_enabled=admin.mfa_enabled,
    )


def require_platform_admin_permission(
    code: str,
) -> Callable[..., Awaitable[PlatformAdminContext]]:
    """Mirrors auth.dependencies.require_permission exactly, against PlatformAdminContext."""

    async def checker(
        current: PlatformAdminContext = Depends(get_current_platform_admin),
    ) -> PlatformAdminContext:
        if code not in current.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current

    return checker


async def get_maintenance_db() -> AsyncGenerator[AsyncSession, None]:
    """See app.db.base.maintenance_session_factory's docstring — full-privilege, RLS-bypassing
    session for platform-wide actions with no single tenant to scope by. Only
    PlatformAdminDataService.purge_all_tenant_data uses this."""

    async with maintenance_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
