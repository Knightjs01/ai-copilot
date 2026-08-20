import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

InterviewStatus = Literal["scheduled", "cancelled", "completed"]


class InterviewCreate(BaseModel):
    scheduled_at: datetime
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=500)


class InterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=500)


class InterviewRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    scheduled_at: datetime
    location: str | None
    meeting_link: str | None
    status: InterviewStatus
    created_at: datetime


class CandidateInterviewSummary(InterviewRead):
    job_title: str
    company_name: str
    callsign: str
