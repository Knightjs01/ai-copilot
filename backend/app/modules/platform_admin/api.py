from typing import Literal

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth.exceptions import InvalidOrExpiredTokenError
from app.modules.platform_admin.dependencies import (
    PlatformAdminContext,
    get_current_platform_admin,
    get_maintenance_db,
    require_platform_admin,
    require_platform_admin_permission,
)
from app.modules.platform_admin.models import PlatformAdmin
from app.modules.platform_admin.permissions import PlatformAdminPermissions
from app.modules.platform_admin.schemas import (
    ChangePasswordRequest,
    CreatePlatformAdminRequest,
    PlatformAdminLoginRequest,
    PlatformAdminRead,
    PlatformAdminSummary,
    PlatformAdminTokenResponse,
    PurgeAllDataRequest,
    PurgeAllDataResult,
)
from app.modules.platform_admin.service import (
    PlatformAdminAuthService,
    PlatformAdminDataService,
    PlatformAdminManagementService,
)

router = APIRouter(prefix="/platform-admin", tags=["platform-admin"])

REFRESH_COOKIE_NAME = "platform_admin_refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    samesite: Literal["none", "lax"] = "none" if settings.cookie_secure else "lax"
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/platform-admin",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/platform-admin")


@router.post("/login", response_model=PlatformAdminTokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    body: PlatformAdminLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> PlatformAdminTokenResponse:
    tokens = await PlatformAdminAuthService(session).login(
        email=body.email, password=body.password
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return PlatformAdminTokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=PlatformAdminTokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_db),
) -> PlatformAdminTokenResponse:
    if refresh_token is None:
        raise InvalidOrExpiredTokenError()

    tokens = await PlatformAdminAuthService(session).refresh(refresh_token_plain=refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return PlatformAdminTokenResponse(access_token=tokens.access_token)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_db),
) -> None:
    if refresh_token is not None:
        await PlatformAdminAuthService(session).logout(refresh_token_plain=refresh_token)
    _clear_refresh_cookie(response)


@router.post("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db),
) -> None:
    await PlatformAdminAuthService(session).change_password(
        admin=admin, current_password=body.current_password, new_password=body.new_password
    )


@router.get("/me", response_model=PlatformAdminRead)
async def me(admin: PlatformAdminContext = Depends(get_current_platform_admin)) -> PlatformAdminRead:
    return PlatformAdminRead(
        id=admin.id,
        email=admin.email,
        full_name=admin.full_name,
        roles=admin.roles,
        permissions=sorted(admin.permissions),
    )


@router.post("/danger-zone/purge", response_model=PurgeAllDataResult)
@limiter.limit("3/minute")
async def purge_all_data(
    request: Request,
    body: PurgeAllDataRequest,
    admin: PlatformAdmin = Depends(require_platform_admin),
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.DANGER_ZONE_PURGE)
    ),
    session: AsyncSession = Depends(get_maintenance_db),
) -> PurgeAllDataResult:
    return await PlatformAdminDataService(session).purge_all_tenant_data(
        admin=admin, password=body.password, confirmation_phrase=body.confirmation_phrase
    )


@router.get("/admins", response_model=list[PlatformAdminSummary])
async def list_admins(
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.ADMINS_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> list[PlatformAdminSummary]:
    return await PlatformAdminManagementService(session).list_admins()


@router.post("/admins", response_model=PlatformAdminSummary, status_code=201)
async def create_admin(
    body: CreatePlatformAdminRequest,
    _: PlatformAdminContext = Depends(
        require_platform_admin_permission(PlatformAdminPermissions.ADMINS_MANAGE)
    ),
    session: AsyncSession = Depends(get_db),
) -> PlatformAdminSummary:
    return await PlatformAdminManagementService(session).create_admin(
        full_name=body.full_name, email=body.email, password=body.password, role_name=body.role
    )
