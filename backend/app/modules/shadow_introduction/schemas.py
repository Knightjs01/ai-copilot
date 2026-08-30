import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.shadow_introduction.models import IntroductionRequestStatus


class IntroductionRequestCreate(BaseModel):
    message: str | None = Field(default=None, max_length=2000)


class IntroductionRequestRead(BaseModel):
    """Company-side view of one request it sent."""

    id: uuid.UUID
    callsign: str
    shadow_job_id: uuid.UUID
    message: str | None
    status: IntroductionRequestStatus
    requested_at: datetime
    responded_at: datetime | None
    resulting_application_id: uuid.UUID | None


class CandidateIntroductionRequestRead(BaseModel):
    """What the candidate sees -- company/role context plus the recruiter's optional message,
    nothing about the request that isn't needed to decide. Showing the real company name and job
    title here is correct and consistent with how Shadow already works -- this product's
    anonymity protects the candidate's identity from the recruiter, not the company's identity
    from the candidate."""

    id: uuid.UUID
    company_name: str
    job_title: str
    message: str | None
    status: IntroductionRequestStatus
    requested_at: datetime
    responded_at: datetime | None
    resulting_application_id: uuid.UUID | None


class IntroductionDecision(BaseModel):
    # No decline-reason field -- matches Talent Pool's precedent of a single-click decline.
    approve: bool
