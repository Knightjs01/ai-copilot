import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CompanySizeBand = Literal["1-10", "11-50", "51-200", "201-500", "500+"]


class ContentItem(BaseModel):
    """A titled, short-body content block -- used for both `values` and `hiring_highlights`.
    Same shape for both since they're presentationally identical (icon+title+body cards);
    keeping one schema avoids two near-duplicate definitions."""

    title: str = Field(max_length=100)
    body: str = Field(max_length=300)


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    email_domain: str
    is_verified_domain: bool
    description: str | None
    culture: str | None
    benefits: list[Any]
    size: str | None
    industry: list[Any]
    logo_url: str | None
    cover_image_url: str | None
    hiring_process_overview: str | None
    profile_status: str
    status: str
    tagline: str | None
    website: str | None
    founded_year: int | None
    headquarters: str | None
    employee_count: int | None
    is_verified_employer: bool
    values: list[Any]
    looking_for: list[Any]
    hiring_highlights: list[Any]


class CompanyUpdate(BaseModel):
    """Every field is genuinely optional and applied only when present in model_fields_set --
    fixes a real pre-existing bug where an omitted field used to silently reset to its default
    (False for is_profile_public, [] for benefits/industry) on every PATCH. is_verified_employer
    is deliberately never here -- a company can never set that on itself, only a platform admin."""

    description: str | None = Field(default=None, max_length=5000)
    culture: str | None = Field(default=None, max_length=5000)
    benefits: list[str] | None = Field(default=None, max_length=50)
    size: CompanySizeBand | None = Field(default=None)
    industry: list[str] | None = Field(default=None, max_length=50)
    hiring_process_overview: str | None = Field(default=None, max_length=5000)
    tagline: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    headquarters: str | None = Field(default=None, max_length=255)
    employee_count: int | None = Field(default=None, ge=0, le=10_000_000)
    values: list[ContentItem] | None = Field(default=None, max_length=12)
    looking_for: list[str] | None = Field(default=None, max_length=20)
    hiring_highlights: list[ContentItem] | None = Field(default=None, max_length=12)


class CompanyProfileRead(BaseModel):
    """Public-facing shape -- no id/email_domain/is_verified_domain, same
    "expose only what's needed" discipline as every other public/anonymized schema. Built from
    either a CompanyProfileVersion snapshot (the real public page) or live draft fields (preview
    mode) -- never from a raw ORM Company object directly, since logo_url/cover_image_url are
    derived, not real columns. is_verified_employer IS included here -- unlike is_verified_domain,
    it's the one verification signal safe and meaningful to show to a candidate."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    description: str | None
    culture: str | None
    benefits: list[Any]
    size: str | None
    industry: list[Any]
    logo_url: str | None
    cover_image_url: str | None
    hiring_process_overview: str | None
    tagline: str | None
    website: str | None
    founded_year: int | None
    headquarters: str | None
    is_verified_employer: bool
    values: list[Any]
    looking_for: list[Any]
    hiring_highlights: list[Any]


class CompanyBoardCard(BaseModel):
    """Lightweight public shape for a browsable company listing (Shadow's "Explore companies") --
    deliberately thinner than CompanyProfileRead, which is for the full detail page. No
    description/culture/benefits/etc: just enough for a card."""

    name: str
    slug: str
    tagline: str | None
    logo_url: str | None
    cover_image_url: str | None
    industry: list[Any]
    employee_count: int | None
    headquarters: str | None
    is_verified_employer: bool


class ProfileReviewRejectBody(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class PublishChangesRequest(BaseModel):
    """Company Onboarding Phase 2's self-publish action -- the checkbox is a real, checked
    field, not just a disabled-until-checked frontend affordance: the backend independently
    refuses to publish without it (see ChangesNotConfirmedError), same discipline as every other
    confirmation step in this codebase (e.g. the purge phrase)."""

    confirmed: bool = Field(default=False)


class AdminCreateCompanyRequest(BaseModel):
    """Company Onboarding Phase 1 -- a platform admin originating a brand-new company with no
    prior access request. commercial_plan_code is optional; omitted, the company gets the same
    default (Core) every self-service-approved company already gets."""

    company_name: str = Field(min_length=1, max_length=200)
    owner_email: str = Field(min_length=3, max_length=320)
    owner_full_name: str = Field(min_length=1, max_length=200)
    commercial_plan_code: str | None = Field(default=None)


class AdminInviteCompanyUserRequest(BaseModel):
    """Mirrors auth.schemas' self-service InviteUserRequest body exactly -- the only difference
    is who's authorized to call it (a platform admin mid-onboarding, not an existing company
    user) and which company_id it targets (from the URL, not the caller's own session)."""

    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=200)
    role_name: str


class AdminCompanySummary(BaseModel):
    """Platform-admin-facing company directory row -- a leaner, distinct shape from CompanyRead
    (that one is for the owning company's own settings page; this includes admin-only fields
    like user_count and never gets returned to a company's own users)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    email_domain: str
    is_verified_domain: bool
    status: str
    profile_status: str
    user_count: int
    created_at: datetime
    commercial_plan_code: str | None
    active_role_limit_override: int | None
    is_verified_employer: bool


class ProfileStats(BaseModel):
    """Internal-only numbers shown on the company's own profile page -- never part of the shared
    public/preview shape above. total_hires is all-time (not "this year") since Candidate has no
    hired-transition timestamp to compute a precise time-boxed figure from -- see the plan this
    shipped under for why an approximate time-boxed number was rejected in favor of an exact
    all-time one. team_size is Company.employee_count directly (a real, company-entered headcount)
    -- deliberately NOT a count of Phantom Hire logins, which is a much smaller, unrelated number;
    null until the company fills it in, never defaulted to 0 (0 would falsely claim "no
    employees" for a company that simply hasn't entered this yet)."""

    active_role_count: int
    total_hires: int
    team_size: int | None
    candidates_in_pipeline: int


class AdminCompanyDetail(AdminCompanySummary):
    """Platform-admin Company Command Profile detail shape -- AdminCompanySummary's admin-only
    fields plus the full profile content CompanyRead carries and the company's own ProfileStats,
    combined into the one call the detail page needs. No new content, just the union of two
    already-real shapes plus already-real stats."""

    description: str | None
    culture: str | None
    benefits: list[Any]
    size: str | None
    industry: list[Any]
    logo_url: str | None
    cover_image_url: str | None
    hiring_process_overview: str | None
    tagline: str | None
    website: str | None
    founded_year: int | None
    headquarters: str | None
    employee_count: int | None
    values: list[Any]
    looking_for: list[Any]
    hiring_highlights: list[Any]
    profile_stats: ProfileStats
