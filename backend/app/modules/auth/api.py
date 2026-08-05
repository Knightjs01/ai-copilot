import uuid

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_current_user_model,
    get_email_sender,
    get_tenant_db,
    require_permission,
)
from app.modules.auth.email import EmailSender
from app.modules.auth.exceptions import InvalidOrExpiredTokenError
from app.modules.auth.models import User
from app.modules.auth.permissions import Permissions
from app.modules.auth.repository.roles import RoleRepository
from app.modules.auth.schemas import (
    AcceptInviteRequest,
    ChangeRoleRequest,
    ForgotPasswordRequest,
    InviteUserRequest,
    LoginRequest,
    MeResponse,
    MfaChallengeResponse,
    MfaDisableRequest,
    MfaEnableRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserRead,
    VerifyEmailRequest,
)
from app.modules.auth.service.auth_service import AuthService, IssuedTokens, MfaChallenge
from app.modules.auth.service.user_service import UserService

router = APIRouter(tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/auth")


def _user_read(user: User, role_names: list[str]) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        roles=role_names,
    )


@router.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    body: SignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> TokenResponse:
    _, tokens = await AuthService(session, email_sender=email_sender).signup(
        company_name=body.company_name,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token)


@router.post("/auth/login", response_model=TokenResponse | MfaChallengeResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse | MfaChallengeResponse:
    result = await AuthService(session).login(email=body.email, password=body.password)
    if isinstance(result, MfaChallenge):
        return MfaChallengeResponse(challenge_token=result.challenge_token)

    tokens: IssuedTokens = result
    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token)


@router.post("/auth/mfa/verify", response_model=TokenResponse)
@limiter.limit("10/minute")
async def verify_mfa(
    request: Request,
    body: MfaVerifyRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    tokens = await AuthService(session).verify_mfa_and_login(
        challenge_token=body.challenge_token, code=body.code
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if refresh_token is None:
        raise InvalidOrExpiredTokenError()

    tokens = await AuthService(session).refresh(refresh_token_plain=refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    session: AsyncSession = Depends(get_db),
) -> None:
    if refresh_token is not None:
        await AuthService(session).logout(refresh_token_plain=refresh_token)
    _clear_refresh_cookie(response)


@router.get("/auth/me", response_model=MeResponse)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    user: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> MeResponse:
    roles = await RoleRepository(session).get_roles_for_user(user.id)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company_id=user.company_id,
        is_email_verified=user.is_email_verified,
        mfa_enabled=user.mfa_enabled,
        roles=[r.name for r in roles],
        permissions=sorted(current_user.permissions),
    )


@router.post("/auth/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(body: VerifyEmailRequest, session: AsyncSession = Depends(get_db)) -> None:
    await AuthService(session).verify_email(token_plain=body.token)


@router.post("/auth/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> None:
    await AuthService(session, email_sender=email_sender).request_email_verification(
        email=body.email
    )


@router.post("/auth/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> None:
    await AuthService(session, email_sender=email_sender).request_password_reset(email=body.email)


@router.post("/auth/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest, session: AsyncSession = Depends(get_db)
) -> None:
    await AuthService(session).reset_password(
        token_plain=body.token, new_password=body.new_password
    )


@router.post("/auth/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    user: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> MfaSetupResponse:
    secret, uri = await AuthService(session).setup_mfa(user=user)
    return MfaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/auth/mfa/enable", status_code=status.HTTP_204_NO_CONTENT)
async def enable_mfa(
    body: MfaEnableRequest,
    user: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await AuthService(session).enable_mfa(user=user, secret=body.secret, code=body.code)


@router.post("/auth/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    body: MfaDisableRequest,
    user: User = Depends(get_current_user_model),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await AuthService(session).disable_mfa(user=user, password=body.password)


@router.post("/users/invite", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def invite_user(
    body: InviteUserRequest,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.USERS_INVITE)),
    session: AsyncSession = Depends(get_tenant_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> UserRead:
    invited = await UserService(session, email_sender=email_sender).invite_user(
        inviter=actor, email=body.email, full_name=body.full_name, role_name=body.role
    )
    return _user_read(invited, [body.role])


@router.post("/users/accept-invite", response_model=TokenResponse)
async def accept_invite(
    body: AcceptInviteRequest, response: Response, session: AsyncSession = Depends(get_db)
) -> TokenResponse:
    tokens = await UserService(session).accept_invite(
        token_plain=body.token, password=body.password, full_name=body.full_name
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token)


@router.get("/users", response_model=list[UserRead])
async def list_users(
    current_user: CurrentUser = Depends(get_current_user),
    _: CurrentUser = Depends(require_permission(Permissions.USERS_VIEW)),
    session: AsyncSession = Depends(get_tenant_db),
) -> list[UserRead]:
    users_with_roles = await UserService(session).list_company_users(
        company_id=current_user.company_id
    )
    return [_user_read(uwr.user, uwr.role_names) for uwr in users_with_roles]


@router.patch("/users/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_role(
    user_id: uuid.UUID,
    body: ChangeRoleRequest,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.USERS_CHANGE_ROLE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await UserService(session).change_user_role(
        actor=actor, target_user_id=user_id, new_role_name=body.role
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    user_id: uuid.UUID,
    actor: User = Depends(get_current_user_model),
    _: CurrentUser = Depends(require_permission(Permissions.USERS_REMOVE)),
    session: AsyncSession = Depends(get_tenant_db),
) -> None:
    await UserService(session).remove_user(actor=actor, target_user_id=user_id)
