from typing import Literal

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth.exceptions import InvalidOrExpiredTokenError
from app.modules.platform_admin.dependencies import get_maintenance_db, require_platform_admin
from app.modules.platform_admin.models import PlatformAdmin
from app.modules.platform_admin.schemas import (
    PlatformAdminLoginRequest,
    PlatformAdminRead,
    PlatformAdminTokenResponse,
    PurgeAllDataRequest,
    PurgeAllDataResult,
)
from app.modules.platform_admin.service import PlatformAdminAuthService, PlatformAdminDataService

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


@router.get("/me", response_model=PlatformAdminRead)
async def me(admin: PlatformAdmin = Depends(require_platform_admin)) -> PlatformAdminRead:
    return PlatformAdminRead(id=admin.id, email=admin.email, full_name=admin.full_name)


@router.post("/danger-zone/purge", response_model=PurgeAllDataResult)
@limiter.limit("3/minute")
async def purge_all_data(
    request: Request,
    body: PurgeAllDataRequest,
    admin: PlatformAdmin = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_maintenance_db),
) -> PurgeAllDataResult:
    return await PlatformAdminDataService(session).purge_all_tenant_data(
        admin=admin, password=body.password, confirmation_phrase=body.confirmation_phrase
    )
