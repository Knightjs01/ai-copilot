import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEntryRead(BaseModel):
    id: uuid.UUID
    actor_email: str | None
    action: str
    target_type: str
    target_id: uuid.UUID | None
    extra_data: dict[str, Any]
    created_at: datetime
