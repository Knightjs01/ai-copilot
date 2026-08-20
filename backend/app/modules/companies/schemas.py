import uuid
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
    is_profile_public: bool


class CompanyUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=5000)
    culture: str | None = Field(default=None, max_length=5000)
    benefits: list[str] = Field(default_factory=list, max_length=50)
    size: CompanySizeBand | None = Field(default=None)
    industry: list[str] = Field(default_factory=list, max_length=50)
    is_profile_public: bool = False


class CompanyProfileRead(BaseModel):
    """Public-facing shape -- no id/email_domain/is_verified_domain, same
    "expose only what's needed" discipline as every other public/anonymized schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    description: str | None
    culture: str | None
    benefits: list[Any]
    size: str | None
    industry: list[Any]
