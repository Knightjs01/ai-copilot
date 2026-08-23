import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.disclosure import DisclosureLevel, IdentityField


class VaultFieldsUpdate(BaseModel):
    """Owner-editable Vault fields — set post-hoc from the Identity Vault tab. Location/current
    employer/current title are not auto-extracted from CV text (no NER in this codebase); best
    a recruiter can do is enter them here if genuinely needed for the reveal snapshot."""

    location: str | None = Field(default=None, max_length=255)
    current_employer: str | None = Field(default=None, max_length=255)
    current_title: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=500)


class IdentitySnapshot(BaseModel):
    """The decrypted Reveal Identity response — the only place vault plaintext ever crosses the
    API boundary. Never cached or logged; the frontend renders it in a dismissable popup only.
    Fields beyond what was disclosed are always None, never omitted — the caller always sees the
    full shape of what it could ask for and what it actually got."""

    reveal_event_id: uuid.UUID
    disclosure_level: DisclosureLevel
    disclosed_fields: list[IdentityField]
    callsign: str
    candidate_ref: str
    full_name: str | None
    email: str | None
    phone: str | None
    location: str | None
    current_employer: str | None
    current_title: str | None
    linkedin_url: str | None
    expected_salary: int | None
    original_cv_status: str = "Not retained"


class RevealRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
    disclosure_level: DisclosureLevel = DisclosureLevel.FULL
    # Explicit field-level override — when given, takes precedence over disclosure_level entirely
    # (must be non-empty). When omitted, disclosure_level's tier default applies exactly as before.
    disclosed_fields: list[IdentityField] | None = None


class RevealCloseRequest(BaseModel):
    duration_seconds: int = Field(ge=0)


class VaultListItem(BaseModel):
    """Covers both an ATS-added Candidate (identity_vault's own reveal flow) and a Shadow
    marketplace applicant on this project's linked Shadow Job (shadow_reveal's consent-gated
    flow) -- two structurally different identity systems, unified here only so an Owner has one
    place to see every real person attached to this project, matching the same merge already
    applied to the project's Candidates tab. `source` tells the frontend which reveal mechanism
    (and which route) applies to this row."""

    source: str  # "ats" | "shadow"
    candidate_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    shadow_job_id: uuid.UUID | None = None
    callsign: str
    candidate_ref: str | None = None
    status: str
    vault_populated: bool


class RevealEventRead(BaseModel):
    """Same ATS/Shadow merge as VaultListItem, applied to the audit trail -- only real reveals
    (identity actually disclosed), never a pending or declined Shadow request, matching this
    tab's stated promise that everything listed here is an actual disclosure event."""

    id: uuid.UUID
    source: str  # "ats" | "shadow"
    candidate_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    shadow_job_id: uuid.UUID | None = None
    callsign: str
    candidate_ref: str | None = None
    actor_email: str
    reason: str
    disclosure_level: DisclosureLevel
    disclosed_fields: list[str] | None = None
    revealed_at: datetime
    closed_at: datetime | None = None
    duration_seconds: int | None = None


class VaultDashboardStats(BaseModel):
    total_candidates: int
    active_vault_records: int
    reveal_event_count: int
    recent_reveals: list[RevealEventRead]
