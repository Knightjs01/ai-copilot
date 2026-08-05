import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.candidates.models import CandidateSource, CandidateStatus


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
    created_by_id: uuid.UUID
