import uuid
from typing import Literal

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth import security
from app.modules.candidate_auth.dependencies import get_current_candidate
from app.modules.candidate_auth.exceptions import CandidateInvalidOrExpiredTokenError
from app.modules.candidate_auth.models import CandidateUser
from app.modules.candidate_auth.schemas import (
    CandidateLoginRequest,
    CandidateMeResponse,
    CandidateMfaChallengeResponse,
    CandidateMfaDisableRequest,
    CandidateMfaEnableRequest,
    CandidateMfaEnableResponse,
    CandidateMfaSetupResponse,
    CandidateMfaVerifyRequest,
    CandidateSessionRead,
    CandidateSignupRequest,
    CandidateTokenResponse,
    CandidateWebAuthnAuthenticationOptionsRequest,
    CandidateWebAuthnAuthenticationVerifyRequest,
    CandidateWebAuthnCredentialRead,
    CandidateWebAuthnOptionsResponse,
    CandidateWebAuthnRegistrationVerifyRequest,
)
from app.modules.candidate_auth.service import CandidateAuthService, CandidateMfaChallenge

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


def _client_context(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


@router.post("/signup", response_model=CandidateTokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    body: CandidateSignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse:
    user_agent, ip_address = _client_context(request)
    _, tokens = await CandidateAuthService(session).signup(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return CandidateTokenResponse(access_token=tokens.access_token)


@router.post("/login", response_model=CandidateTokenResponse | CandidateMfaChallengeResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: CandidateLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse | CandidateMfaChallengeResponse:
    user_agent, ip_address = _client_context(request)
    result = await CandidateAuthService(session).login(
        email=body.email, password=body.password, user_agent=user_agent, ip_address=ip_address
    )
    if isinstance(result, CandidateMfaChallenge):
        return CandidateMfaChallengeResponse(challenge_token=result.challenge_token)

    _set_refresh_cookie(response, result.refresh_token)
    return CandidateTokenResponse(access_token=result.access_token)


@router.post("/mfa/verify", response_model=CandidateTokenResponse)
@limiter.limit("10/minute")
async def verify_mfa(
    request: Request,
    body: CandidateMfaVerifyRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse:
    user_agent, ip_address = _client_context(request)
    tokens = await CandidateAuthService(session).verify_mfa_and_login(
        challenge_token=body.challenge_token,
        code=body.code,
        user_agent=user_agent,
        ip_address=ip_address,
    )
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

    user_agent, ip_address = _client_context(request)
    tokens = await CandidateAuthService(session).refresh(
        refresh_token_plain=refresh_token, user_agent=user_agent, ip_address=ip_address
    )
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
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        is_email_verified=candidate.is_email_verified,
        mfa_enabled=candidate.mfa_enabled,
    )


@router.post("/mfa/setup", response_model=CandidateMfaSetupResponse)
@limiter.limit("10/minute")
async def setup_mfa(
    request: Request,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CandidateMfaSetupResponse:
    secret, uri = await CandidateAuthService(session).setup_mfa(candidate=candidate)
    return CandidateMfaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/mfa/enable", response_model=CandidateMfaEnableResponse)
@limiter.limit("10/minute")
async def enable_mfa(
    request: Request,
    body: CandidateMfaEnableRequest,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CandidateMfaEnableResponse:
    backup_codes = await CandidateAuthService(session).enable_mfa(
        candidate=candidate, secret=body.secret, code=body.code
    )
    return CandidateMfaEnableResponse(backup_codes=backup_codes)


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def disable_mfa(
    request: Request,
    body: CandidateMfaDisableRequest,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> None:
    await CandidateAuthService(session).disable_mfa(candidate=candidate, password=body.password)


@router.get("/sessions", response_model=list[CandidateSessionRead])
async def list_sessions(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
) -> list[CandidateSessionRead]:
    current_hash = security.hash_opaque_token(refresh_token) if refresh_token else None
    sessions = await CandidateAuthService(session).list_sessions(candidate)
    return [
        CandidateSessionRead(
            id=s.id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            is_current=s.token_hash == current_hash,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: uuid.UUID,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> None:
    await CandidateAuthService(session).revoke_session(candidate=candidate, session_id=session_id)


@router.post("/sessions/revoke-others", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_other_sessions(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE_NAME),
) -> None:
    await CandidateAuthService(session).revoke_other_sessions(
        candidate=candidate, current_refresh_token_plain=refresh_token
    )


@router.post("/webauthn/register/options", response_model=CandidateWebAuthnOptionsResponse)
@limiter.limit("10/minute")
async def webauthn_register_options(
    request: Request,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CandidateWebAuthnOptionsResponse:
    options_json = await CandidateAuthService(session).begin_webauthn_registration(
        candidate=candidate
    )
    return CandidateWebAuthnOptionsResponse(options=options_json)


@router.post("/webauthn/register/verify", response_model=CandidateWebAuthnCredentialRead)
@limiter.limit("10/minute")
async def webauthn_register_verify(
    request: Request,
    body: CandidateWebAuthnRegistrationVerifyRequest,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> CandidateWebAuthnCredentialRead:
    credential = await CandidateAuthService(session).complete_webauthn_registration(
        candidate=candidate, credential_json=body.credential, device_name=body.device_name
    )
    return CandidateWebAuthnCredentialRead(
        id=credential.id,
        device_name=credential.device_name,
        created_at=credential.created_at,
        last_used_at=credential.last_used_at,
    )


@router.get("/webauthn/credentials", response_model=list[CandidateWebAuthnCredentialRead])
async def list_webauthn_credentials(
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> list[CandidateWebAuthnCredentialRead]:
    credentials = await CandidateAuthService(session).list_webauthn_credentials(candidate=candidate)
    return [
        CandidateWebAuthnCredentialRead(
            id=c.id, device_name=c.device_name, created_at=c.created_at, last_used_at=c.last_used_at
        )
        for c in credentials
    ]


@router.delete("/webauthn/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webauthn_credential(
    credential_id: uuid.UUID,
    candidate: CandidateUser = Depends(get_current_candidate),
    session: AsyncSession = Depends(get_db),
) -> None:
    await CandidateAuthService(session).delete_webauthn_credential(
        candidate=candidate, credential_pk_id=credential_id
    )


@router.post("/webauthn/authenticate/options", response_model=CandidateWebAuthnOptionsResponse)
@limiter.limit("10/minute")
async def webauthn_authenticate_options(
    request: Request,
    body: CandidateWebAuthnAuthenticationOptionsRequest,
    session: AsyncSession = Depends(get_db),
) -> CandidateWebAuthnOptionsResponse:
    options_json = await CandidateAuthService(session).begin_webauthn_authentication(
        email=body.email
    )
    return CandidateWebAuthnOptionsResponse(options=options_json)


@router.post("/webauthn/authenticate/verify", response_model=CandidateTokenResponse)
@limiter.limit("10/minute")
async def webauthn_authenticate_verify(
    request: Request,
    body: CandidateWebAuthnAuthenticationVerifyRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> CandidateTokenResponse:
    user_agent, ip_address = _client_context(request)
    tokens = await CandidateAuthService(session).complete_webauthn_authentication(
        email=body.email,
        credential_json=body.credential,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return CandidateTokenResponse(access_token=tokens.access_token)
