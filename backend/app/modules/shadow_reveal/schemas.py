import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.disclosure import DisclosureLevel, ShadowField
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


class CandidateRevealHistoryItem(BaseModel):
    """One row in the candidate-wide 'Identity Activity' timeline -- same job/company context
    as CandidateRevealRequestRead, plus the full lifecycle (responded_at, and exactly which
    fields were disclosed when approved) since this view spans every application, not just the
    one currently being decided."""

    id: uuid.UUID
    shadow_application_id: uuid.UUID
    job_title: str
    company_name: str
    reason: str | None
    status: RevealRequestStatus
    requested_at: datetime
    responded_at: datetime | None
    # Null while pending/declined. Populated on approval; disclosed_fields is only ever set when
    # the candidate explicitly narrowed disclosure (disclosure_level="custom") -- a routine full
    # approval stores the level but leaves disclosed_fields null, see respond_to_reveal_request.
    disclosure_level: DisclosureLevel | None
    disclosed_fields: list[ShadowField] | None


class RevealDecision(BaseModel):
    approve: bool
    # The candidate's own choice of how much to disclose — only meaningful when approve=True.
    # Unlike identity_vault's disclosure_level (an Owner deciding how much to see), this is the
    # candidate deciding how much to give: they can approve a reveal while still withholding
    # contact details or career history if all the company needs is confirmation of interest.
    disclosure_level: DisclosureLevel = DisclosureLevel.FULL
    # Explicit field-level override — when given, takes precedence over disclosure_level entirely
    # (must be non-empty). When omitted, disclosure_level's tier default applies exactly as before.
    disclosed_fields: list[ShadowField] | None = None


class RevealedCareerEntry(BaseModel):
    title: str
    company_name: str
    is_current: bool
    start_date: date | None = None
    end_date: date | None = None
    responsibilities: str | None = None
    achievements: list[str] = Field(default_factory=list)


class RevealedIdentity(BaseModel):
    """The minimum-necessary disclosure snapshot — see shadow_reveal/__init__.py for what is and
    isn't included and why. Fields beyond what disclosure_level grants are always None/empty,
    never omitted from the response shape."""

    application_id: uuid.UUID
    disclosure_level: DisclosureLevel
    disclosed_fields: list[ShadowField]
    callsign: str
    full_name: str | None
    email: str | None
    phone: str | None
    career_entries: list[RevealedCareerEntry]
    revealed_at: datetime
