import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth import security
from app.modules.auth.dependencies import get_bearer_token
from app.modules.platform_admin.models import PlatformAdmin
from app.modules.platform_admin.repository import PlatformAdminRepository


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
