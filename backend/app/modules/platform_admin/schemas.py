import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.shadow_jobs.schemas import ShadowJobRead


class PlatformAdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class PlatformAdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PlatformAdminMfaChallengeResponse(BaseModel):
    # Discriminator field the frontend checks for -- mirrors auth.schemas.MfaChallengeResponse.
    mfa_required: bool = True
    challenge_token: str


class PlatformAdminMfaEnrollmentRequiredResponse(BaseModel):
    # Discriminator field the frontend checks for, distinct from mfa_required above so the two
    # branches (already enrolled vs. must enroll now) can never be confused for one another.
    mfa_enrollment_required: bool = True
    pending_token: str


class PlatformAdminMfaVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=11)


class PlatformAdminPendingMfaSetupRequest(BaseModel):
    pending_token: str


class PlatformAdminPendingMfaEnableRequest(BaseModel):
    pending_token: str
    secret: str
    code: str


class PlatformAdminEnrollAndLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    backup_codes: list[str]


class PlatformAdminRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    roles: list[str] = []
    permissions: list[str] = []
    mfa_enabled: bool = False


class PlatformAdminMfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class PlatformAdminMfaEnableRequest(BaseModel):
    secret: str
    code: str


class PlatformAdminMfaEnableResponse(BaseModel):
    backup_codes: list[str]


class PlatformAdminMfaDisableRequest(BaseModel):
    password: str


class PlatformAdminStepUpRequest(BaseModel):
    password: str
    mfa_code: str | None = None


class PlatformAdminStepUpResponse(BaseModel):
    step_up_token: str


class PlatformAdminSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[str]
    created_at: datetime


class CreatePlatformAdminRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str


class AdminShadowJobRead(ShadowJobRead):
    company_name: str


class RejectShadowJobRequest(BaseModel):
    reason: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class PurgeAllDataRequest(BaseModel):
    # No password field -- superseded by the step-up token this route now requires (see
    # require_platform_admin_step_up), which already re-verified password + MFA moments ago.
    confirmation_phrase: str


class PurgeAllDataResult(BaseModel):
    tables_cleared: int


class PlatformAdminAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    admin_id: uuid.UUID
    action: str
    target_type: str
    target_id: uuid.UUID | None
    extra_data: dict[str, Any]
    created_at: datetime
