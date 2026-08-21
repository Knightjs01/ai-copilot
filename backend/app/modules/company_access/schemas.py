import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyAccessRequestCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    work_email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class CompanyAccessRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    job_title: str | None
    company_name: str
    work_email: str
    status: str
    created_at: datetime


class RejectAccessRequestBody(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class RequestInfoBody(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class AccessRequestStatsRead(BaseModel):
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    active_companies: int
    suspended_companies: int
