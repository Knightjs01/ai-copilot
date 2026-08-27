import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


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
