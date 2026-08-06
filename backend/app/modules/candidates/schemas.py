import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.candidates.models import CandidateSource, CandidateStatus, PrescreenOutcome


class CandidateCreate(BaseModel):
    project_id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    source: CandidateSource = CandidateSource.DIRECT
    status: CandidateStatus = CandidateStatus.NEW


class CandidateUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    source: CandidateSource | None = None
    status: CandidateStatus | None = None
    interview_scheduled_at: datetime | None = None
    prescreen_outcome: PrescreenOutcome | None = None
    prescreen_notes: str | None = None
    expected_salary: int | None = Field(default=None, ge=0)
    agency_name: str | None = Field(default=None, max_length=255)


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    project_id: uuid.UUID
    full_name: str
    email: str | None
    phone: str | None
    source: CandidateSource
    status: CandidateStatus
    resume_original_filename: str | None
    interview_scheduled_at: datetime | None
    prescreen_outcome: PrescreenOutcome | None
    prescreen_notes: str | None
    expected_salary: int | None
    agency_name: str | None
    created_by_id: uuid.UUID
