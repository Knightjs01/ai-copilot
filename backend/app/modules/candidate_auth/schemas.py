import uuid

from pydantic import BaseModel, EmailStr, Field


class CandidateSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)


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


class CandidateMeResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_email_verified: bool
    mfa_enabled: bool
