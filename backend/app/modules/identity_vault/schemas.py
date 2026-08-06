import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.candidates.models import CandidateStatus


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
    API boundary. Never cached or logged; the frontend renders it in a dismissable popup only."""

    reveal_event_id: uuid.UUID
    callsign: str
    candidate_ref: str
    full_name: str
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


class RevealCloseRequest(BaseModel):
    duration_seconds: int = Field(ge=0)


class VaultListItem(BaseModel):
    candidate_id: uuid.UUID
    callsign: str
    candidate_ref: str
    status: CandidateStatus
    vault_populated: bool


class RevealEventRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    callsign: str
    candidate_ref: str
    actor_email: str
    reason: str
    revealed_at: datetime
    closed_at: datetime | None
    duration_seconds: int | None


class VaultDashboardStats(BaseModel):
    total_candidates: int
    active_vault_records: int
    reveal_event_count: int
    recent_reveals: list[RevealEventRead]
