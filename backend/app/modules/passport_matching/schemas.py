import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.talent_pool.models import TalentPoolScope

MatchTier = Literal["Excellent Match", "Strong Match", "Potential Match", "Weak Match"]


class PassportJobMatchRead(BaseModel):
    job_id: uuid.UUID
    match_tier: MatchTier
    match_score: int
    strengths: list[str]
    gaps: list[str]
    summary: str
    generated_at: datetime


class BatchMatchRequest(BaseModel):
    shadow_job_ids: list[uuid.UUID] = Field(min_length=1, max_length=24)


class SearchQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class BoardFilters(BaseModel):
    """Mirrors the real filter params GET /shadow-jobs/board already accepts — natural-language
    search only ever fills in a subset of these, never invents a fifth filter the board doesn't
    support."""

    seniority: str | None = None
    remote_preference: str | None = None
    employment_type: str | None = None
    location: str | None = None


class CandidateSearchCareerEntry(BaseModel):
    title: str
    company_name_anonymized: str
    is_current: bool


class CandidateSearchResult(BaseModel):
    """One discoverable candidate ranked against a company's job — see
    PassportMatchingService.search_candidates_for_job. Deliberately has no field that could hold
    a name, email, phone, or real employer, same discipline as shadow_jobs.schemas.ShadowProfile.
    `match_summary` (not `summary`) to avoid colliding with the passport's own bio `summary`
    field in this flat response."""

    callsign: str
    headline: str | None
    seniority: str | None
    years_experience: int | None
    summary: str | None
    skills: list[str]
    industries: list[str]
    location: str | None
    remote_preference: str | None
    salary_min: int | None
    salary_max: int | None
    notice_period: str | None
    career_intent: str
    career_entries: list[CandidateSearchCareerEntry]
    match_tier: MatchTier
    match_score: int
    match_summary: str
    strengths: list[str]
    gaps: list[str]


class TalentPoolMatchResult(CandidateSearchResult):
    """A Talent Pool candidate ranked against a NEW role — same shape as CandidateSearchResult,
    plus the grant context that makes this result meaningful (spec: "you previously considered
    this candidate for..."). See PassportMatchingService.search_talent_pool_for_job."""

    source_role_title: str
    scope: TalentPoolScope
    granted_at: datetime


class TalentPoolOpportunity(BaseModel):
    """The candidate's own view of a real match a company computed against their Talent Pool
    grant — not anonymized (this is the candidate looking at their own data), and includes a
    real, still-applyable job to view/apply to. See
    PassportMatchingService.list_talent_pool_opportunities."""

    job_id: uuid.UUID
    job_title: str
    company_name: str
    match_tier: MatchTier
    match_score: int
    match_summary: str
    strengths: list[str]
    gaps: list[str]
    generated_at: datetime
