import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class CandidateSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)


class CandidateLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CandidateTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CandidateMfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    challenge_token: str


class CandidateMfaVerifyRequest(BaseModel):
    challenge_token: str
    # 6 for a TOTP code, or 11 ("XXXXX-XXXXX") for an MFA backup recovery code — see
    # CandidateAuthService.verify_mfa_and_login, which tries TOTP first, backup code second.
    code: str = Field(min_length=6, max_length=11)


class CandidateMfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class CandidateMfaEnableRequest(BaseModel):
    secret: str
    code: str = Field(min_length=6, max_length=6)


class CandidateMfaEnableResponse(BaseModel):
    backup_codes: list[str]


class CandidateMfaDisableRequest(BaseModel):
    password: str


class CandidateResendVerificationRequest(BaseModel):
    email: EmailStr


class CandidateVerifyEmailRequest(BaseModel):
    token: str


class CandidateMeResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str | None
    is_email_verified: bool
    mfa_enabled: bool


class CandidateSessionRead(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    last_used_at: datetime | None
    is_current: bool


class CandidateWebAuthnOptionsResponse(BaseModel):
    options: str


class CandidateWebAuthnRegistrationVerifyRequest(BaseModel):
    credential: dict[str, Any]
    device_name: str | None = Field(default=None, max_length=255)


class CandidateWebAuthnAuthenticationOptionsRequest(BaseModel):
    email: EmailStr


class CandidateWebAuthnAuthenticationVerifyRequest(BaseModel):
    email: EmailStr
    credential: dict[str, Any]


class CandidateWebAuthnCredentialRead(BaseModel):
    id: uuid.UUID
    device_name: str | None
    created_at: datetime
    last_used_at: datetime | None
