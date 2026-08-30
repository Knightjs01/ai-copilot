import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.modules.passport_matching.schemas import MatchTier, PassReason

TimelineEventType = Literal[
    "application_submitted",
    "reveal_requested",
    "reveal_responded",
    "talent_pool_requested",
    "talent_pool_responded",
    "talent_pool_withdrawn",
    "passed",
    "introduction_requested",
    "introduction_responded",
    "conversation_started",
]


class TimelineEntry(BaseModel):
    """One real event in a company<->candidate relationship. `description` is always a short,
    plain-language summary built server-side -- never raw message content, even for the
    company's own conversation threads, so this stays a scannable feed, not a transcript.
    `callsign` is populated only on the company-wide feed (list_recent_company_activity); the
    per-candidate timeline caller already knows who they're looking at."""

    event_type: TimelineEventType
    description: str
    occurred_at: datetime
    callsign: str | None = None


class RediscoveryCandidate(BaseModel):
    """A candidate this company passed on whose Passport has materially changed since. `changes`
    is never empty -- diff_passport_snapshots returning [] means "skip," not "show with nothing
    to say." See CandidatePass's own docstring for why job_id-null passes are company-wide and
    job_id-set passes are role-specific -- both can be rediscovered."""

    callsign: str
    headline: str | None
    seniority: str | None
    changes: list[str]
    passed_reason: PassReason | None
    passed_shadow_job_id: uuid.UUID | None
    passed_for_job_title: str | None
    passed_at: datetime


class AiRecommendation(BaseModel):
    """One real, evidence-backed suggestion -- the same MatchTier/match_score every other
    surface in this product already uses, never a new scoring concept. Deliberately thin: it
    links back into the real search/Quick View flow rather than duplicating its content."""

    job_id: uuid.UUID
    job_title: str
    callsign: str
    match_tier: MatchTier
    match_score: int
    match_summary: str
