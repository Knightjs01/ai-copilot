import uuid
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

# Bounds each item's length, not just the list length — a single 5MB string as one "skill" would
# otherwise still slip through a bare max_length=N on the list itself.
_ShortListItem = Annotated[str, Field(max_length=200)]


class CareerEntryInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    company_name_anonymized: str = Field(min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    responsibilities: str | None = Field(default=None, max_length=5000)
    achievements: list[_ShortListItem] = Field(default_factory=list, max_length=50)


class CareerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company_name: str
    company_name_anonymized: str
    start_date: date | None
    end_date: date | None
    is_current: bool
    responsibilities: str | None
    achievements: list[str]


class PersonalInfoInput(BaseModel):
    legal_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)


class PersonalInfoRead(BaseModel):
    legal_name: str
    phone: str | None
    address: str | None


class PassportUpdate(BaseModel):
    headline: str | None = Field(default=None, max_length=255)
    seniority: str | None = Field(default=None, max_length=100)
    years_experience: int | None = Field(default=None, ge=0, le=70)
    summary: str | None = Field(default=None, max_length=5000)
    skills: list[_ShortListItem] = Field(default_factory=list, max_length=100)
    industries: list[_ShortListItem] = Field(default_factory=list, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    remote_preference: str | None = Field(default=None, max_length=100)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    notice_period: str | None = Field(default=None, max_length=100)
    career_intent: str | None = Field(default=None, max_length=100)
    personal_info: PersonalInfoInput
    career_entries: list[CareerEntryInput] = Field(default_factory=list, max_length=50)


class PassportRead(BaseModel):
    id: uuid.UUID
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
    verification_status: str
    completion_percentage: int
    # Non-null iff the candidate has explicitly approved a snapshot — see PassportVersion. A
    # Shadow application can't be submitted until this is set. Draft edits after approval don't
    # clear this — the last-approved version keeps being what new applications use until the
    # candidate explicitly re-approves.
    current_version_number: int | None
    # Generated once, at first approval — a stable identity for the Passport itself, distinct
    # from shadow_jobs' per-application Callsigns. Only ever returned here, to the owning
    # candidate — never added to ShadowProfileSnapshot or any other company-facing schema.
    callsign: str | None
    personal_info: PersonalInfoRead
    career_entries: list[CareerEntryRead]


class CvParseCareerEntry(BaseModel):
    title: str
    company_name: str
    company_name_anonymized: str
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    responsibilities: str | None = None
    achievements: list[str] = Field(default_factory=list)


class CvParseResult(BaseModel):
    """A preview only — nothing from this response is persisted until the candidate submits it
    (possibly edited) via PUT /phantom-passport/me. See phantom_passport/__init__.py.

    ai_suggested_fields names the top-level/career-entry fields that are Phantom AI's own
    normalization rather than text lifted directly from the CV (e.g. `industries` is an inferred
    categorization, `company_name_anonymized` is an AI-generated descriptor) — everything else
    with a value is a direct extraction. A coarse, field-name-level distinction, not per-token
    provenance: the LLM extraction has no token-level confidence data to draw a finer line."""

    headline: str | None
    seniority: str | None
    years_experience: int | None
    summary: str | None
    skills: list[str]
    industries: list[str]
    career_entries: list[CvParseCareerEntry]
    detected_phone: str | None
    detected_address: str | None
    ai_suggested_fields: list[str] = Field(
        default_factory=lambda: ["industries", "company_name_anonymized"]
    )


class CvDocumentRead(BaseModel):
    original_filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime


class PassportVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    approved_at: datetime
    source_cv_filename: str | None


class SummaryImprovementRequest(BaseModel):
    headline: str | None = Field(default=None, max_length=255)
    summary: str = Field(min_length=1, max_length=5000)
    skills: list[_ShortListItem] = Field(default_factory=list, max_length=100)


class SummaryImprovementResponse(BaseModel):
    # A suggestion only — the candidate applies or dismisses it client-side, exactly like
    # ai_suggested_fields from CV parsing. Never written to the Passport by this endpoint.
    suggested_summary: str


class SkillsSuggestionRequest(BaseModel):
    headline: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=5000)
    existing_skills: list[_ShortListItem] = Field(default_factory=list, max_length=100)


class SkillsSuggestionResponse(BaseModel):
    suggested_skills: list[str]


class ShadowProfileSnapshot(BaseModel):
    """The exact shape persisted into PassportVersion.snapshot — see
    shadow_jobs/schemas.py::ShadowProfile, which this deliberately mirrors field-for-field (minus
    the per-application fields like application_id/callsign/status that don't belong in a
    Passport-level snapshot). schema_version lets old snapshots stay renderable if this shape
    ever changes."""

    schema_version: int = 1
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
    career_entries: list[dict[str, Any]]
