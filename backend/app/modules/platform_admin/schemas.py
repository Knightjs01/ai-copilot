import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.shadow_jobs.schemas import ShadowJobRead


class PlatformAdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class PlatformAdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PlatformAdminRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    roles: list[str] = []
    permissions: list[str] = []


class PlatformAdminSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    roles: list[str]
    created_at: datetime


class CreatePlatformAdminRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str


class AdminShadowJobRead(ShadowJobRead):
    company_name: str


class RejectShadowJobRequest(BaseModel):
    reason: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class PurgeAllDataRequest(BaseModel):
    password: str
    confirmation_phrase: str


class PurgeAllDataResult(BaseModel):
    tables_cleared: int


class PlatformAdminAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    admin_id: uuid.UUID
    action: str
    target_type: str
    target_id: uuid.UUID | None
    extra_data: dict[str, Any]
    created_at: datetime
