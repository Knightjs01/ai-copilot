import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.shadow_reveal.models import RevealRequestStatus


class RevealRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class RevealRequestRead(BaseModel):
    id: uuid.UUID
    shadow_application_id: uuid.UUID
    callsign: str
    reason: str | None
    status: RevealRequestStatus
    requested_at: datetime
    responded_at: datetime | None


class CandidateRevealRequestRead(BaseModel):
    """What the candidate sees before deciding — job/company context plus the company's stated
    reason, but nothing about the request that isn't needed to make the decision."""

    id: uuid.UUID
    shadow_application_id: uuid.UUID
    job_title: str
    company_name: str
    reason: str | None
    status: RevealRequestStatus
    requested_at: datetime


class RevealDecision(BaseModel):
    approve: bool


class RevealedCareerEntry(BaseModel):
    title: str
    company_name: str
    is_current: bool


class RevealedIdentity(BaseModel):
    """The minimum-necessary disclosure snapshot — see shadow_reveal/__init__.py for what is and
    isn't included and why."""

    application_id: uuid.UUID
    callsign: str
    full_name: str
    email: str
    phone: str | None
    career_entries: list[RevealedCareerEntry]
    revealed_at: datetime
