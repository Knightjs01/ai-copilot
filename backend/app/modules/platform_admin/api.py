from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.platform_admin.dependencies import require_platform_admin
from app.modules.platform_admin.models import PlatformAdmin
from app.modules.platform_admin.schemas import (
    PlatformAdminLoginRequest,
    PlatformAdminRead,
    PlatformAdminTokenResponse,
)
from app.modules.platform_admin.service import PlatformAdminAuthService

router = APIRouter(prefix="/platform-admin", tags=["platform-admin"])


@router.post("/login", response_model=PlatformAdminTokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: PlatformAdminLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> PlatformAdminTokenResponse:
    access_token = await PlatformAdminAuthService(session).login(
        email=body.email, password=body.password
    )
    return PlatformAdminTokenResponse(access_token=access_token)


@router.get("/me", response_model=PlatformAdminRead)
async def me(admin: PlatformAdmin = Depends(require_platform_admin)) -> PlatformAdminRead:
    return PlatformAdminRead(id=admin.id, email=admin.email, full_name=admin.full_name)
