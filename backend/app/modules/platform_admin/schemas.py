import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.shadow_jobs.schemas import JobIntelligence, ShadowJobRead


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


class AdminShadowJobDetail(AdminShadowJobRead):
    match_count: int
    interview_count: int
    job_intelligence: JobIntelligence | None


class AdminShadowJobListResponse(BaseModel):
    """Real server-side pagination for the platform-admin Jobs list -- see
    AdminCompanyListResponse (companies/schemas.py) for why items+total replaces the old bare
    array response."""

    items: list[AdminShadowJobRead]
    total: int


class RejectShadowJobRequest(BaseModel):
    reason: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class PasswordResetConfirmRequest(BaseModel):
    reset_token: str
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


class PlatformAdminAuditLogListResponse(BaseModel):
    """Real server-side pagination for the Activity page -- see the identically-shaped
    AdminCompanyListResponse (companies/schemas.py) from the prior phase."""

    items: list[PlatformAdminAuditLogRead]
    total: int


class PlatformAdminNotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: str
    title: str
    body: str
    target_type: str
    target_id: uuid.UUID | None
    created_at: datetime


class PlatformAdminNotificationListResponse(BaseModel):
    items: list[PlatformAdminNotificationRead]
    total: int
    unread_count: int


class PlatformAdminUnreadNotificationCountResponse(BaseModel):
    unread_count: int


class AdminCandidateSummary(BaseModel):
    """Platform-admin Candidate Command list row -- anonymous professional data only, the same
    boundary ShadowProfile already enforces elsewhere. Never a name, email, or phone."""

    id: uuid.UUID
    callsign: str | None
    headline: str | None
    seniority: str | None
    verification_status: str
    visibility: str
    career_intent: str
    created_at: datetime


class AdminCandidateListResponse(BaseModel):
    """Real server-side pagination for the platform-admin Candidates list -- see
    AdminCompanyListResponse (companies/schemas.py) for why items+total replaces the old bare
    array response."""

    items: list[AdminCandidateSummary]
    total: int


class AdminCandidateCareerEntry(BaseModel):
    title: str
    company_name_anonymized: str
    start_date: date | None
    end_date: date | None
    is_current: bool
    responsibilities: str | None
    achievements: list[Any]


class AdminCandidateApplication(BaseModel):
    """Real, cross-company application data -- companies are never anonymized in this product
    (only candidates are), so this is genuine platform-oversight data, not an identity leak."""

    shadow_job_id: uuid.UUID
    job_title: str
    company_id: uuid.UUID
    company_name: str
    status: str
    pipeline_stage: str
    created_at: datetime


class AdminCandidateDetail(AdminCandidateSummary):
    years_experience: int | None
    summary: str | None
    skills: list[Any]
    industries: list[Any]
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    notice_period: str | None
    career_entries: list[AdminCandidateCareerEntry]
    applications: list[AdminCandidateApplication]
