import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    challenge_token: str


class MfaVerifyRequest(BaseModel):
    challenge_token: str
    # 6 for a TOTP code, or 11 ("XXXXX-XXXXX") for an MFA backup recovery code — see
    # AuthService.verify_mfa_and_login, which tries TOTP first and falls back to a backup code.
    code: str = Field(min_length=6, max_length=11)


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    company_id: uuid.UUID
    is_email_verified: bool
    mfa_enabled: bool
    roles: list[str]
    permissions: list[str]


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=255)


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaEnableRequest(BaseModel):
    secret: str
    code: str = Field(min_length=6, max_length=6)


class MfaEnableResponse(BaseModel):
    backup_codes: list[str]


class MfaDisableRequest(BaseModel):
    password: str


class StepUpRequest(BaseModel):
    password: str
    # Required only if the account has MFA enrolled — AuthService.step_up enforces that, not
    # this schema, since whether it's required depends on the authenticated user, not the shape
    # of the request. Accepts a TOTP code or an "XXXXX-XXXXX" backup code, same as mfa/verify.
    mfa_code: str | None = Field(default=None, min_length=6, max_length=11)


class StepUpResponse(BaseModel):
    step_up_token: str


class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: str


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=255)
    full_name: str | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_email_verified: bool
    roles: list[str]


class ChangeRoleRequest(BaseModel):
    role: str


class SessionRead(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    last_used_at: datetime | None
    is_current: bool


class WebAuthnOptionsResponse(BaseModel):
    # Raw JSON string from py_webauthn's options_to_json — passed through untouched so the
    # frontend hands it directly to the browser's navigator.credentials.create()/get() calls.
    options: str


class WebAuthnRegistrationVerifyRequest(BaseModel):
    credential: dict[str, Any]
    device_name: str | None = Field(default=None, max_length=255)


class WebAuthnAuthenticationOptionsRequest(BaseModel):
    email: EmailStr


class WebAuthnAuthenticationVerifyRequest(BaseModel):
    email: EmailStr
    credential: dict[str, Any]


class WebAuthnCredentialRead(BaseModel):
    id: uuid.UUID
    device_name: str | None
    created_at: datetime
    last_used_at: datetime | None
