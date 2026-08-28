import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CompanySizeBand = Literal["1-10", "11-50", "51-200", "201-500", "500+"]


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


class CompanyUpdate(BaseModel):
    """Every field is genuinely optional and applied only when present in model_fields_set --
    fixes a real pre-existing bug where an omitted field used to silently reset to its default
    (False for is_profile_public, [] for benefits/industry) on every PATCH."""

    description: str | None = Field(default=None, max_length=5000)
    culture: str | None = Field(default=None, max_length=5000)
    benefits: list[str] | None = Field(default=None, max_length=50)
    size: CompanySizeBand | None = Field(default=None)
    industry: list[str] | None = Field(default=None, max_length=50)
    hiring_process_overview: str | None = Field(default=None, max_length=5000)


class CompanyProfileRead(BaseModel):
    """Public-facing shape -- no id/email_domain/is_verified_domain, same
    "expose only what's needed" discipline as every other public/anonymized schema. Built from
    either a CompanyProfileVersion snapshot (the real public page) or live draft fields (preview
    mode) -- never from a raw ORM Company object directly, since logo_url/cover_image_url are
    derived, not real columns."""

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


class ProfileReviewRejectBody(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


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
