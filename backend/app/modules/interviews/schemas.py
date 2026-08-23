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
    company_name is omitted (every row is already this company's own). project_id lets the
    frontend deep-link into the job's linked Project when one exists; shadow_job_id is always
    present and is what the frontend actually needs to reach this interview's own detail page
    and act on it (scorecard/cancel/complete), independent of whether a Project link exists."""

    job_title: str
    callsign: str
    project_id: uuid.UUID | None
    shadow_job_id: uuid.UUID


CompetencyRating = Literal["Strong", "Moderate", "Weak"]
OverallRecommendation = Literal["Strong Hire", "Hire", "No Hire", "Strong No Hire"]


class CompetencyScore(BaseModel):
    competency: str
    rating: CompetencyRating
    evidence: str


class InterviewScorecardGenerateRequest(BaseModel):
    notes: str = Field(min_length=1)


class InterviewScorecardDraft(BaseModel):
    """A generated-but-not-yet-saved preview -- mirrors the JdUploadResult/CvParseResult
    "preview, review, then explicit save" pattern already established elsewhere in this
    codebase. Nothing is persisted until the interviewer POSTs InterviewScorecardSave."""

    competency_scores: list[CompetencyScore]
    overall_recommendation: OverallRecommendation
    summary: str


class InterviewScorecardSave(BaseModel):
    notes: str = Field(min_length=1)
    competency_scores: list[CompetencyScore] = Field(min_length=1)
    overall_recommendation: OverallRecommendation


class InterviewScorecardRead(BaseModel):
    id: uuid.UUID
    interview_id: uuid.UUID
    submitted_by_user_id: uuid.UUID
    notes: str
    competency_scores: list[CompetencyScore]
    overall_recommendation: OverallRecommendation
    model_used: str
    generated_at: datetime
