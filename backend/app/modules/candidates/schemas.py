import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.candidates.models import (
    CandidateSource,
    CandidateStatus,
    NoticePeriod,
    PrescreenOutcome,
)


class CandidateCreate(BaseModel):
    project_id: uuid.UUID
    # Input-only — CandidateService routes these straight into a new Identity Vault record and
    # never persists them on the Candidate row itself. See app/modules/identity_vault/__init__.py.
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    source: CandidateSource = CandidateSource.DIRECT
    status: CandidateStatus = CandidateStatus.NEW


class CandidateUpdate(BaseModel):
    source: CandidateSource | None = None
    status: CandidateStatus | None = None
    interview_scheduled_at: datetime | None = None
    prescreen_outcome: PrescreenOutcome | None = None
    prescreen_notes: str | None = None
    expected_salary: int | None = Field(default=None, ge=0)
    agency_name: str | None = Field(default=None, max_length=255)
    notice_period: NoticePeriod | None = None


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    project_id: uuid.UUID
    callsign: str
    candidate_ref: str
    source: CandidateSource
    status: CandidateStatus
    resume_original_filename: str | None
    interview_scheduled_at: datetime | None
    prescreen_outcome: PrescreenOutcome | None
    prescreen_notes: str | None
    expected_salary: int | None
    agency_name: str | None
    notice_period: NoticePeriod | None
    created_by_id: uuid.UUID
    # True once at least one Identity Vault reveal event has ever fired for this candidate --
    # not derived from a column on Candidate itself (see identity_vault module docstring), so
    # this is always explicitly computed by the API layer, never left to default.
    is_revealed: bool
