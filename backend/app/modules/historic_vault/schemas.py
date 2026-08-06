import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PurgedProjectRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    project_title: str
    candidate_count: int
    data_categories_destroyed: list[str]
    purged_by_email: str
    purged_at: datetime


class AuditLogEntryRead(BaseModel):
    id: uuid.UUID
    actor_email: str | None
    action: str
    target_type: str
    target_id: uuid.UUID | None
    extra_data: dict[str, Any]
    created_at: datetime


class HistoricVaultOverview(BaseModel):
    purged_project_count: int
    purged_projects: list[PurgedProjectRecordRead]
    recent_audit_entries: list[AuditLogEntryRead]
