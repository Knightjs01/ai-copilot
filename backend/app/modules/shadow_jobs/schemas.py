import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.shadow_jobs.models import (
    EmploymentType,
    ShadowApplicationStatus,
    ShadowJobStatus,
    ShadowPipelineStage,
)


class ShadowJobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    seniority: str | None = Field(default=None, max_length=100)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    location: str | None = Field(default=None, max_length=255)
    remote_preference: str | None = Field(default=None, max_length=20)
    salary_min: int | None = None
    salary_max: int | None = None
    summary: str = Field(min_length=1)
    description: str = Field(min_length=1)
    requirements: list[Any] = Field(default_factory=list)
    project_id: uuid.UUID | None = None


class ShadowJobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = None
    seniority: str | None = None
    employment_type: EmploymentType | None = None
    location: str | None = None
    remote_preference: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    summary: str | None = None
    description: str | None = None
    requirements: list[Any] | None = None


class ShadowJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    department: str | None
    seniority: str | None
    employment_type: str
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    summary: str
    description: str
    requirements: list[Any]
    status: ShadowJobStatus
    published_at: datetime | None
    applicant_count: int = 0


class ShadowJobBoardListing(BaseModel):
    """Public job board card/detail — same shape for the list and the single-job view. Company
    identity is shown by name deliberately: Shadow anonymizes the CANDIDATE to the recruiter,
    not the employer to the candidate (candidates choose to apply, or not, knowing who's
    hiring)."""

    id: uuid.UUID
    company_name: str
    # None unless the company's profile page is currently live (Company.profile_status == "live")
    # -- fails open, no link shown, otherwise.
    company_slug: str | None
    title: str
    department: str | None
    seniority: str | None
    employment_type: str
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    summary: str
    description: str
    requirements: list[Any]
    published_at: datetime | None


class ShadowApplicationCreate(BaseModel):
    """Empty on purpose — "one-click apply": the candidate applies with whatever their Phantom
    Passport already holds, nothing new to fill in at apply time."""


class ShadowApplicationRead(BaseModel):
    id: uuid.UUID
    shadow_job_id: uuid.UUID
    job_title: str
    company_name: str
    callsign: str
    status: ShadowApplicationStatus
    applied_at: datetime


class ShadowCareerEntrySummary(BaseModel):
    title: str
    company_name_anonymized: str
    is_current: bool


class ShadowProfile(BaseModel):
    """The recruiter-facing anonymized applicant card. Deliberately has no field that could hold
    a name, email, phone, or real employer — see shadow_jobs/__init__.py for how that's enforced
    structurally, not just by what this schema happens to list."""

    application_id: uuid.UUID
    callsign: str
    status: ShadowApplicationStatus
    applied_at: datetime
    headline: str | None
    seniority: str | None
    years_experience: int | None
    summary: str | None
    skills: list[Any]
    industries: list[Any]
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    notice_period: str | None
    career_intent: str
    career_entries: list[ShadowCareerEntrySummary]
    unread_message_count: int = 0
    has_upcoming_interview: bool = False
    # None when no Talent Pool request has ever been made for this candidate at this company —
    # see talent_pool/service.py. A bulk lookup, same shape as unread_message_count above.
    talent_pool_status: str | None = None
    # Recruiter-set hiring-pipeline progress -- independent of `status` above, which is
    # identity-reveal workflow state only. See ShadowPipelineStage's docstring in models.py.
    pipeline_stage: str
    # `pipeline_stage`, unless the candidate has withdrawn -- withdrawal is candidate-initiated
    # only and always overrides wherever the application sat in the pipeline (computed, never
    # persisted as pipeline_stage="withdrawn", so a withdrawn candidate's last real stage isn't
    # destroyed). This is the field the merged Kanban board actually groups by.
    effective_stage: str
    # True until a recruiter opens this applicant's card for the first time (viewed_at is None).
    # Powers the "New application" badge on the Kanban/applicant-list surfaces.
    is_new: bool = False


class ShadowApplicantPipelineUpdate(BaseModel):
    pipeline_stage: ShadowPipelineStage


class AddFromTalentPoolRequest(BaseModel):
    """Recruiter-triggered application on behalf of an already-granted Talent Pool candidate --
    callsign is re-resolved to a candidate_user_id server-side (never trusted from the client),
    same discipline as TalentPoolBulkRequestCreate."""

    callsign: str


class ShadowProfileCompanyWide(ShadowProfile):
    """Same shape as ShadowProfile, plus which job/project this application belongs to -- powers
    the company-wide Candidates/Pipeline merge, where (unlike a single job's applicant list) the
    job context isn't already implied by the URL."""

    shadow_job_id: uuid.UUID
    job_title: str
    project_id: uuid.UUID | None
