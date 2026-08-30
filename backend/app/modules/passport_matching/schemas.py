import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.talent_pool.models import TalentPoolScope

MatchTier = Literal["Excellent Match", "Strong Match", "Potential Match", "Weak Match"]
DimensionRatingValue = Literal["Strong", "Moderate", "Weak"]

# Computed per (company, candidate) at search time -- never persisted as its own row, always
# derived fresh from the real ShadowApplication/TalentPoolGrant/CandidatePass/IntroductionRequest
# signals that already exist, so it can never drift from the truth. Priority order when multiple
# signals exist: currently_engaged > in_talent_pool > introduction_pending > previously_passed >
# previously_applied > introduction_declined > new. A pending introduction is a live, unanswered
# ask the recruiter must not duplicate, so it ranks just under an existing pool relationship; a
# declined introduction is a real but softer signal than an outright applied/passed state, so it
# sits just above the default. An *accepted* introduction needs no value of its own here -- it
# auto-creates a real ShadowApplication (see shadow_introduction.service), which this same
# priority chain already surfaces as previously_applied/currently_engaged with no extra code.
RelationshipStatus = Literal[
    "new",
    "previously_applied",
    "previously_passed",
    "in_talent_pool",
    "currently_engaged",
    "introduction_pending",
    "introduction_declined",
]


class DimensionRating(BaseModel):
    """One row of the real per-dimension match breakdown -- always grounded in an evidence
    sentence naming the actual values compared, never a bare label. Location/Compensation/
    Seniority are computed deterministically (see PassportMatchingService._deterministic_
    dimensions); Role alignment/Industry experience/Functional experience come from the LLM's own
    forced-tool-call response, same discipline as strengths/gaps."""

    dimension: str
    rating: DimensionRatingValue
    evidence: str


class PassportJobMatchRead(BaseModel):
    job_id: uuid.UUID
    match_tier: MatchTier
    match_score: int
    strengths: list[str]
    gaps: list[str]
    summary: str
    dimension_breakdown: list[DimensionRating]
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
    dimension_breakdown: list[DimensionRating]
    relationship_status: RelationshipStatus


class TalentPoolMatchResult(CandidateSearchResult):
    """A Talent Pool candidate ranked against a NEW role — same shape as CandidateSearchResult,
    plus the grant context that makes this result meaningful (spec: "you previously considered
    this candidate for..."). See PassportMatchingService.search_talent_pool_for_job."""

    source_role_title: str
    scope: TalentPoolScope
    granted_at: datetime


PassReason = Literal[
    "insufficient_experience",
    "too_senior",
    "too_junior",
    "wrong_sector",
    "wrong_location",
    "compensation_mismatch",
    "skills_mismatch",
    "not_relevant",
    "already_engaged",
    "role_filled",
    "other",
]


class CandidatePassRequest(BaseModel):
    # Scoped to this one job when set; a null job_id means "not right for us generally," excluded
    # from every future search for this company, not just this role.
    job_id: uuid.UUID | None = None
    reason: PassReason | None = None


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
    dimension_breakdown: list[DimensionRating]
    generated_at: datetime
