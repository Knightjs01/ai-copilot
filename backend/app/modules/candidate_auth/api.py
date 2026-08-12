from typing import Literal

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.candidate_auth.dependencies import get_current_candidate
from app.modules.candidate_auth.exceptions import CandidateInvalidOrExpiredTokenError
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.schemas import (
    CandidateLoginRequest,
    CandidateMeResponse,
    CandidateSignupRequest,
    CandidateTokenResponse,
)
from app.modules.candidate_auth.service import CandidateAuthService

router = APIRouter(prefix="/candidate-auth", tags=["candidate-auth"])

_REFRESH_COOKIE_NAME = "candidate_refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/candidate-auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    samesite: Literal["none", "lax"] = "none" if settings.cookie_secure else "lax"
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE_NAME, path=_REFRESH_COOKIE_PATH)


@router.post("/signup", response_model=CandidateTokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    body: CandidateSignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse:
    _, tokens = await CandidateAuthService(session).signup(
        email=body.email, password=body.password, full_name=body.full_name
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return CandidateTokenResponse(access_token=tokens.access_token)


@router.post("/login", response_model=CandidateTokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: CandidateLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse:
    tokens = await CandidateAuthService(session).login(email=body.email, password=body.password)
    _set_refresh_cookie(response, tokens.refresh_token)
    return CandidateTokenResponse(access_token=tokens.access_token)


@router.post("/refresh", response_model=CandidateTokenResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse:
    if refresh_token is None:
        raise CandidateInvalidOrExpiredTokenError()

    tokens = await CandidateAuthService(session).refresh(refresh_token_plain=refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return CandidateTokenResponse(access_token=tokens.access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_db),
) -> None:
    if refresh_token is not None:
        await CandidateAuthService(session).logout(refresh_token_plain=refresh_token)
    _clear_refresh_cookie(response)


@router.get("/me", response_model=CandidateMeResponse)
async def me(candidate: CandidateUser = Depends(get_current_candidate)) -> CandidateMeResponse:
    return CandidateMeResponse(
        id=candidate.id,
        email=candidate.email,
        full_name=candidate.full_name,
        is_email_verified=candidate.is_email_verified,
    )
