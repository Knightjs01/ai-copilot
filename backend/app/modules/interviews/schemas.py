import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

InterviewStatus = Literal["scheduled", "cancelled", "completed"]


class InterviewCreate(BaseModel):
    scheduled_at: datetime
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=500)
    interviewer_user_ids: list[uuid.UUID] = Field(default_factory=list)


class InterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=500)
    interviewer_user_ids: list[uuid.UUID] | None = None


class InterviewRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    scheduled_at: datetime
    location: str | None
    meeting_link: str | None
    status: InterviewStatus
    created_at: datetime
    interviewer_user_ids: list[uuid.UUID]


class CandidateInterviewSummary(InterviewRead):
    job_title: str
    company_name: str
    callsign: str


class CompanyInterviewSummary(InterviewRead):
    """Powers the company-wide Interviews nav destination -- unlike CandidateInterviewSummary,
    company_name is omitted (every row is already this company's own) and project_id is included
    so the frontend can deep-link into the job's linked Project (?tab=interviews) when one
    exists."""

    job_title: str
    callsign: str
    project_id: uuid.UUID | None
