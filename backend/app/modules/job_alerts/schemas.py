import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobAlertCreate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    seniority: str | None = Field(default=None, max_length=100)
    remote_preference: str | None = Field(default=None, max_length=20)
    employment_type: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=255)


class JobAlertUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    seniority: str | None = None
    remote_preference: str | None = Field(default=None, max_length=20)
    employment_type: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class JobAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str | None
    seniority: str | None
    remote_preference: str | None
    employment_type: str | None
    location: str | None
    is_active: bool
    created_at: datetime
