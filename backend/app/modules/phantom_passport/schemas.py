import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CareerEntryInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    company_name_anonymized: str = Field(min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    responsibilities: str | None = None
    achievements: list[str] = Field(default_factory=list)


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
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=255)
    remote_preference: str | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    notice_period: str | None = None
    career_intent: str | None = None
    personal_info: PersonalInfoInput
    career_entries: list[CareerEntryInput] = Field(default_factory=list)


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
    (possibly edited) via PUT /phantom-passport/me. See phantom_passport/__init__.py."""

    headline: str | None
    seniority: str | None
    years_experience: int | None
    summary: str | None
    skills: list[str]
    industries: list[str]
    career_entries: list[CvParseCareerEntry]
    detected_phone: str | None
    detected_address: str | None
